import os from 'os'
import path from 'path'

import { logger } from './log.js'
import { RunStep, Mapping, readConfig, Target } from './config.js'
import type { BundleConfig, Package } from './config.js'
import { runSimple } from './run.js'
import { matchPlatformArch, getFilter } from './filter.js'
import { writeArchive } from './archive.js'
import { pack } from './caxa.js'
import { updateHash } from './update-hash.js'
import { symlink } from './symlink.js'
import { PackageReolver } from './PackageResolver.js'

export type { BundleConfig, Pattern, RunStep, PlatformArch } from './config.js'

const log = logger('main');

const toMapping = (mappings: Mapping[], platform: string, arch: string) => {
  const targetMappings = mappings.filter(mapping => matchPlatformArch(mapping, platform, arch))
  targetMappings.forEach(mapping => log.info(`Map '${mapping.from}' -> '${mapping.to}'`))
  return (name: string) => {
    let result = name;
    targetMappings.forEach(({ from, to }) => {
      result = result.replace(from, to)
    })
    return result
  }
}

const runSteps = async (steps: RunStep[], platform: string, arch: string) => {
  const matching = steps.filter(step => matchPlatformArch(step, platform, arch))
  for (const step of matching) {
    await runSimple(step.command)
  }
}

const filterTargets = (targets: Target[], filter: string | undefined) => {
  if (!filter) {
    return targets
  }

  const whitelist = filter.split(',')
  return targets.filter(target => {
    const platformArch = `${target.platform}-${target.arch}`
    return whitelist.indexOf(platformArch) >= 0
  })
}

const filterPackages = (packages: Package[], platform: string, arch: string): string[] => {
  return packages.filter(p => matchPlatformArch(p, platform, arch)).map(entry => entry.name)
}

const toPackagePlatform = (platform: string) => platform == 'win' ? 'win32' : platform

export interface BundleOptions {
  baseDir?: string
  version: string
  snapshot?: string
  bundleConfig?: BundleConfig
  bundleFile?: string
  filter?: string
  noBefore?: boolean
  noRun?: boolean
  hostPlattform?: string
  hostArch?: string
}

export const bundle = async (options: BundleOptions): Promise<void> => {
  const { bundleFile, version } = options;
  const host = {
    platform: options.hostPlattform || os.platform(),
    arch: options.hostArch || os.arch()
  }
  const dir = options.baseDir || process.cwd()
  const config = options.bundleConfig || await readConfig(path.join(dir, bundleFile || 'bundle.yml'), host.platform, host.arch)

  const { output, targets, before, run, packages, includes, excludes, map } = config;

  if (!options.noBefore) {
    await runSteps(before, host.platform, host.arch)
  }

  const outputDir = path.join(output.dir, version)
  const snapshot = options.snapshot || ''
  const archivePrefix = output.prefix
  const hashAlgorithm = 'sha256'
  const hashFile = path.join(outputDir, 'sha256sums.txt')

  const filteredTargets = filterTargets(targets, options.filter)
  for (const target of filteredTargets) {
    log.info(`Bundling target ${target.platform}-${target.arch}`)
    const isWin = target.platform.startsWith('win')

    const fileBase = `${output.name}-${version}${snapshot}-${target.platform}-${target.arch}`;
    const archiveFile = path.join(outputDir, `${fileBase}.tar.gz`);
    const binFile = path.join(outputDir, `${fileBase}${isWin ? '.exe' : ''}`);

    const linkBase = `${output.name}-${snapshot ? `${version}-latest` : 'latest'}-${target.platform}-${target.arch}`;
    const archiveLatestLink = path.join(output.dir, 'latest', `${linkBase}.tar.gz`);
    const binLatestLink = path.join(output.dir, 'latest', `${linkBase}${isWin ? '.exe' : ''}`);

    if (!options.noRun) {
      await runSteps(run, target.platform, target.arch)
    }

    const targetPackages = filterPackages(packages, target.platform, target.arch)
    const packageResolver = new PackageReolver(dir)
    await packageResolver.addPackages(targetPackages, dir, {platform: toPackagePlatform(target.platform), arch: target.arch})
    const packageFiles = (await packageResolver.files).map(file => path.relative(dir, file))
    log.info(`Require ${packageResolver.packageCount} packages with ${packageFiles.length} files for ${targetPackages.length} main packages`)

    const filter = getFilter(packageFiles, includes, excludes, target.platform, target.arch)
    const mapping = toMapping(map, target.platform, target.arch)

    await writeArchive(dir, filter, mapping, archivePrefix, archiveFile)
    await updateHash(archiveFile, hashAlgorithm, `${archiveFile}.${hashAlgorithm}sum`)
    await updateHash(archiveFile, hashAlgorithm, hashFile)
    await symlink(archiveFile, archiveLatestLink).catch(err => log.warn(err, `Could not create symlink from ${archiveFile} to ${archiveLatestLink}`))
    log.info(`Created archive ${archiveFile}`)

    if (Array.isArray(target.command)) {
      const sanitizeVersion = `${version}${snapshot}`.replaceAll(/[^-.A-Za-z0-9]+/g, '-').replaceAll(/-+/g, '-').replace(/(^-|-$)/g, '')
      await pack(archiveFile, archivePrefix, `${output.name}/${sanitizeVersion}`, target.platform, target.command, binFile)
      await updateHash(binFile, hashAlgorithm, `${binFile}.${hashAlgorithm}sum`)
      await updateHash(binFile, hashAlgorithm, hashFile)
      await symlink(binFile, binLatestLink).catch(err => log.warn(err, `Could not create symlink from ${binFile} to ${binLatestLink}`))
      log.info(`Created binary ${binFile}`)
    }

  }
}
