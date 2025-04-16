import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

export const getPluginFiles = () => {
  return [
    path.resolve(__dirname, 'media/map-media.js'),
  ]
}