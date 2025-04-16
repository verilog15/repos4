import path from 'path'
import process from 'process'
import os from 'os'

import { findConfig } from './find-config.js'
import { readConfig } from './read.js'
import { validateConfig } from './validate.js'

export const load = async (file, required = true, autoConfig = true) => {
  let foundConfig = false
  if (!file && autoConfig) {
    foundConfig = await findConfig().catch(() => false)
  }
  const autoConfigFile = foundConfig && (!file || path.resolve(file) == path.resolve(foundConfig))
  if (!file && !foundConfig) {
    if (required) {
      throw new Error(`No configuration could be found. Please initialize a configuration via ./gallery.js run init`)
    }
    return {
      configFile: null,
      config: {},
      autoConfigFile: false,
      configEnv: {}
    }
  }

  const env = {...process.env,
    HOME: process.env.HOME  || os.homedir()
  }
  const configFile = file || foundConfig
  const config = await readConfig(configFile, env)
  await validateConfig(config)
  return {
    configFile,
    config,
    autoConfigFile,
    configEnv: !autoConfigFile && configFile ? {GALLERY_CONFIG: configFile} : {}
  }
}
