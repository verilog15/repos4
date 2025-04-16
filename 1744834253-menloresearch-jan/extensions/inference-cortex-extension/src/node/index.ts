import path from 'path'
import { appResourcePath, getJanDataFolderPath, log } from '@janhq/core/node'
import { ProcessWatchdog } from './watchdog'

let watchdog: ProcessWatchdog | undefined = undefined

/**
 * Spawns a Nitro subprocess.
 * @returns A promise that resolves when the Nitro subprocess is started.
 */
function run(): Promise<any> {
  log(`[CORTEX]:: Spawning cortex subprocess...`)

  return new Promise<void>(async (resolve, reject) => {
    // let gpuVisibleDevices = systemInfo?.gpuSetting?.gpus_in_use.join(',') ?? ''
    let binaryName = `cortex-server${
      process.platform === 'win32' ? '.exe' : ''
    }`
    const binPath = path.join(__dirname, '..', 'bin')

    const executablePath = path.join(binPath, binaryName)

    addEnvPaths(binPath)

    const sharedPath = path.join(appResourcePath(), 'shared')
    // Execute the binary
    log(`[CORTEX]:: Spawn cortex at path: ${executablePath}`)

    const dataFolderPath = getJanDataFolderPath()
    if (watchdog) {
      watchdog.terminate()
    }

    // The HOST address to use for the cortex subprocess
    const LOCAL_PORT = CORTEX_API_URL.split(':').pop() ?? '39291'

    watchdog = new ProcessWatchdog(
      executablePath,
      [
        '--start-server',
        '--port',
        LOCAL_PORT.toString(),
        '--config_file_path',
        `${path.join(dataFolderPath, '.janrc')}`,
        '--data_folder_path',
        dataFolderPath,
        'config',
        '--api_keys',
        process.env.appToken ?? 'cortex.cpp',
      ],
      {
        env: {
          ...process.env,
          // CUDA_VISIBLE_DEVICES: gpuVisibleDevices,
          // // Vulkan - Support 1 device at a time for now
          // ...(gpuVisibleDevices?.length > 0 && {
          //   GGML_VK_VISIBLE_DEVICES: gpuVisibleDevices,
          // }),
        },
        cwd: sharedPath,
      }
    )
    watchdog.start()
    resolve()
  })
}

/**
 * Every module should have a dispose function
 * This will be called when the extension is unloaded and should clean up any resources
 * Also called when app is closed
 */
function dispose() {
  watchdog?.terminate()
}

/**
 * Set the environment paths for the cortex subprocess
 * @param dest
 */
function addEnvPaths(dest: string) {
  // Add engine path to the PATH and LD_LIBRARY_PATH
  if (process.platform === 'win32') {
    process.env.PATH = (process.env.PATH || '').concat(path.delimiter, dest)
  } else {
    process.env.LD_LIBRARY_PATH = (process.env.LD_LIBRARY_PATH || '').concat(
      path.delimiter,
      dest
    )
  }
}

/**
 * Cortex process info
 */
export interface CortexProcessInfo {
  isRunning: boolean
}

export default {
  run,
  dispose,
}
