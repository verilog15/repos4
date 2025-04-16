import path from 'path'
import chokidar from 'chokidar'

import Logger from '@home-gallery/logger'

import { CliProcessManager } from '../utils/cli-process-manager.js'

const log = Logger('cli.task.import')

const pm = new CliProcessManager()

const updateIndex = async (source, options) => {
  const { journal, smallFiles, addLimits, maxFilesize } = options
  const args = ['index', '--directory', source.dir, '--index', source.index]
  source.matcher && args.push('--matcher', source.matcher)
  source.excludeFromFile && args.push('--exclude-from-file', source.excludeFromFile)
  source.excludeIfPresent && args.push('--exclude-if-present', source.excludeIfPresent)

  const excludes = source.excludes || [];
  excludes.forEach(exclude => args.push('--exclude', exclude))

  if (maxFilesize || source.maxFilesize || smallFiles) {
    args.push('--max-filesize', maxFilesize || source.maxFilesize || '20M')
  }
  addLimits && args.push('--add-limits', addLimits || '200,500,1.25,8000')
  journal && args.push('--journal', journal)
  await pm.runCli(args, {env: options.configEnv, terminateTimeout: 15 * 1000})
}

const updateIndices = async (sources, options) => {
  for (const source of sources) {
    await updateIndex(source, options);
  }
}

const applyJournal = async (source, options) => {
  const { journal } = options
  const args = ['index', 'journal', '--index', source.index, '--journal', journal, 'apply']
  await pm.runCli(args, {env: options.configEnv})
}

const applyJournals = async (sources, options) => {
  if (!options.journal) {
    return
  }
  log.debug(`Applying file index journals`)
  for (const source of sources) {
    await applyJournal(source, options);
  }
}

const removeJournal = async (source, options, force) => {
  const { journal } = options
  const args = ['index', 'journal', '--index', source.index, '--journal', journal, 'remove']
  await pm.runCli(args, {env: options.configEnv}, force)
}

const removeJournals = async (sources, options, force) => {
  if (!options.journal) {
    return
  }
  log.debug(`Removing file index journals`)
  for (const source of sources) {
    await removeJournal(source, options, force)
  }
}

export const extract = async (sources, options) => {
  if (!sources.length) {
    log.warn(`Sources list is empty. No files to extract`);
    return;
  }
  const args = ['extract'];
  sources.forEach(source => args.push('--index', source.index));
  options.journal && args.push('--journal', options.journal)

  options.checksumFrom && args.push('--checksum-from', options.checksumFrom)
  if (options.concurrent) {
    args.push('--concurrent', options.concurrent)
    args.push('--skip', options.skip || 0)
    args.push('--limit', options.limit || 0)
  }

  await pm.runCli(args, {env: options.configEnv})
}

export const createDatabase = async (sources, options) => {
  const args = ['database', 'create'];

  sources.forEach(source => args.push('--index', source.index));
  if (options.journal) {
    args.push('--journal', options.journal)
  }

  const maxMemory = options.config.database?.maxMemory || 2048;
  const nodeArgs = maxMemory ? [`--max-old-space-size=${maxMemory}`] : [];
  await pm.runCli(args, {env: options.configEnv, terminateTimeout: 2000, nodeArgs});
}

const catchIndexLimitExceeded = (err) => {
  const { code } = err
  if (typeof code != 'number') {
    throw new Error(`Updating file index failed: ${err}`, {cause: err})
  }

  if (code == 1) {
    return true
  }
  throw new Error(`Updating file index failed. Exit code is ${code}`)
}

const generateId = len => {
  let id = '';
  while (id.length < len) {
    const c = String.fromCharCode(+(Math.random()*255).toFixed())
    if (c.match(/[0-9A-Za-z]/)) {
      id += c
    }
  }
  return id
}

const pad2 = s => ('' + s).padStart(2, '0')

const generateJournal = () => {
  const now = new Date();
  return `${pad2(now.getUTCMonth() + 1)}${pad2(now.getUTCDate())}-${generateId(4)}`
}

export const importSources = async (sources, options) => {
  let processing = true
  const { initialImport, incrementalUpdate } = options
  const withJournal = initialImport || incrementalUpdate

  log.info(`Import files from source dirs: ${sources.map(source => source.dir).join(', ')}`)
  while (processing && !pm.isStopped) {
    const journal = withJournal ? generateJournal() : false
    const importOptions = { ...options, journal }
    await updateIndices(sources, importOptions)
      .then(() => processing = false)
      .catch(catchIndexLimitExceeded)
    await extract(sources, importOptions)
      .then(() => createDatabase(sources, importOptions))
      .then(() => applyJournals(sources, importOptions))
      .catch(err => {
        log.warn(err, `Import failed: ${err}`)
        return removeJournals(sources, importOptions, true)
      })

    if (processing) {
      log.info(`New chunk of media is processed and becomes ready to browse. Continue with next chunk to process...`)
    }
  }
}

const batchProfiles = [
  {
    description: `Import files up to 20 MB`,
    addLimits: '10,20,1.2,200',
    maxFilesize: '20M'
  },
  {
    description: `Import files up to 200 MB`,
    addLimits: '2,5,1.1,30',
    maxFilesize: '200M'
  },
  {
    description: `Import all remaining files larger than 200 MB`,
    addLimits: '1,2,1.05,10',
  }
]

const batchImport = async (sources, options) => {
  const { initialImport } = options
  const t0 = Date.now()
  if (!initialImport) {
    await importSources(sources, options)
  } else {
    log.info(`Run incremental import in batch mode of different file sizes`)
    for (const profile of batchProfiles) {
      log.info(`Run batch import: ${profile.description}`)
      await importSources(sources, {...options, ...profile})
    }
  }
  log.debug(t0, `Import of online sources finished`)
}

export const watchSources = async (sources, options) => {
  const { watch, watchDelay, watchMaxDelay, watchPollInterval, importOnWatchStart } = options
  if (!watch) {
    return batchImport(sources, options)
  }

  let isImporting = false
  let isInitializing = true
  let fileChangeCount = 0
  let sourcesQueue = []
  const sourceDirs = sources.map(source => source.dir)

  log.info(`Run import in watch mode. Start watching source dirs for file changes: ${sourceDirs.join(', ')}`)
  const usePolling = watchPollInterval > 0
  const chokidarOptions = {
    followSymlinks: true,
    ignoreInitial: true,
    ignorePermissionErrors: true,
    usePolling,
    interval: usePolling ? watchPollInterval * 1000 : 100,
    binaryInterval: usePolling ? watchPollInterval * 1000 : 300
  }
  log.trace({chokidarOptions}, `Use chokidar as file watcher ${usePolling ? 'with polling' : 'with fs events'}`)
  let watcher = chokidar.watch(sourceDirs, chokidarOptions)

  const runImport = async () => {
    if (isImporting) {
      return
    }
    isImporting = true
    fileChangeCount = 0
    const importSources = sourcesQueue.length ? sourcesQueue : sources
    sourcesQueue = []
    return batchImport(importSources, options)
      .then(() => {
        isImporting = false
        if (fileChangeCount > 0) {
          log.info(`Re-run import due ${fileChangeCount} queued file changes`)
          return runImport()
        }
      })
  }

  const queueSourceOf = file => {
    const source = sources.find(source => file.startsWith(path.resolve(source.dir)))
    if (source && !sourcesQueue.includes(source)) {
      sourcesQueue.push(source)
      log.debug(`Queue source ${source.dir} for next import`)
    }
  }

  const createChangeDelay = (delay, maxDelay, onChange) => {
    let firstChangeMs
    let timerId

    const clearTimer = () => clearTimeout(timerId)
    process.once('SIGINT', clearTimer)

    return (event, file) => {
      if (fileChangeCount == 0) {
        firstChangeMs = Date.now()
      }
      fileChangeCount++
      const importDelay = Math.min(Math.max(0, firstChangeMs + maxDelay - Date.now()), delay)
      log.trace(`File change detected: ${event} at ${file}. Delay import by ${importDelay}ms`)
      queueSourceOf(path.resolve(file))
      clearTimer()
      timerId = setTimeout(() => {
        if (!fileChangeCount) {
          return
        } else if (!isImporting) {
          onChange()
        } else {
          log.debug(`Queue file change due running import`)
        }
      }, importDelay)
    }
  }

  return new Promise((resolve, reject) => {
    const importErrorHandler = err => {
      isImporting = false
      log.error(err, `Failed to import: ${err}`);
      log.info(`Stop watching files due error`)
      return watcher.close().then(() => reject(err))
    }

    const onReady = () => {
      isInitializing = false
      log.debug(`File watcher is initialized`)
      if (importOnWatchStart) {
        runImport().catch(importErrorHandler)
      }
    }

    const onDelayChange = () => {
      log.debug(`Run import due ${fileChangeCount} file changes`)
      runImport().catch(importErrorHandler)
    }

    const createFallbackWatcher = () => {
      const pollingOptions = {...chokidarOptions,
        usePolling: true,
        interval: 5 * 60 * 1000,
        binaryInterval: 5 * 60 * 1000
      }

      log.trace({chokidarOptions: pollingOptions}, `Use chokidar as file watcher with fallback polling`)
      watcher = chokidar.watch(sourceDirs, pollingOptions)

      watcher.on('ready', onReady)
      watcher.on('all', createChangeDelay(30 * 1000, 30 * 1000, onDelayChange))
      watcher.on('error', onError)
    }

    const onError = err => {
      watcher.close().then(() => {
        fileChangeCount = 0
        if (err.code == 'ENOSPC' && !usePolling) {
          log.warn(err, `System limit for file watcher exceeded. Increase limit or use polling mode to fix it. Fallback to file watcher with poll interval of 5 min`)
          createFallbackWatcher()
        } else {
          log.error(err, `Stop watcher due watch error ${err}`)
          reject(err)
        }
      })
    }

    watcher.on('ready', onReady)
    watcher.on('all', createChangeDelay(watchDelay, watchMaxDelay, onDelayChange))
    watcher.on('error', onError)

    const shutdown = () => {
      log.info(`Stopping file watcher`)
      Promise.all([watcher.close(), pm.killAll('SIGINT')])
        .then(() => {
          fileChangeCount = 0
          resolve()
        })
    }

    process.once('SIGINT', shutdown)

    process.on('SIGUSR1', () => log.info(`File watcher status: ${isInitializing ? 'initializing' : (isImporting ? 'importing' : 'idle')}`))
  })
}
