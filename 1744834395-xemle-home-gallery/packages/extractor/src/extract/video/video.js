import ffmpeg from 'fluent-ffmpeg';

import Logger from '@home-gallery/logger'
import { humanizeBytes, humanizeDuration } from '@home-gallery/common';

import { getFfmpegArgs, getVideoStream, getVideoDuration } from './video-utils.js'
import { toPlugin } from '../pluginUtils.js';

const log = Logger('extractor.video');

/**
 * @param {import('@home-gallery/types').TExtractorEntry} entry
 * @param {string} src
 * @param {string} dst
 * @param {string} ffmpegPath
 * @param {string} ffprobePath
 * @param {string[]} ffmpegArgs
 */
function convertVideo(entry, src, dst, ffmpegPath, ffprobePath, ffmpegArgs, cb) {
  const intervalMs = 30*1000;
  let last = Date.now();

  const command = ffmpeg(src);
  command.setFfmpegPath(ffmpegPath);
  command.setFfprobePath(ffprobePath);
  command
    .on('error', cb)
    .on('end', cb)
    .addOptions(ffmpegArgs)
    .output(dst)
    .on('start', commandLine => log.debug({ffmpegArgs}, `Start video conversion via ffmpeg command: ${commandLine}`))
    .on('progress', progress => {
      const now = Date.now();
      if (now > last + intervalMs) {
        const optionalPercent = progress.percent ? ` is ${progress.percent?.toFixed()}%` : '';
        log.info(`Video conversion of ${entry} at ${progress.timemark}${optionalPercent} done`);
        last = now;
      }
    })
    .run();
}

const createVideoConverter = (ffmpegPath, ffprobePath, options) => {
  return async (entry, dst) => {
    const src = await entry.getFile()
    const ffmpegArgs = getFfmpegArgs(entry, options)
    return new Promise((resolve, reject) => {
      convertVideo(entry, src, dst, ffmpegPath, ffprobePath, ffmpegArgs, err => err ? reject(err) : resolve())
    })
  }
}

/**
 * @param {import('@home-gallery/types').TStorage} storage
 * @param {string} ffmpegPath
 * @param {string} ffprobePath
 * @param {object} options
 * @returns {import('stream').Transform}
 */
async function video(storage, videoConverter, videoSuffix) {

  const test = entry => entry.type === 'video' && !storage.hasFile(entry, videoSuffix) && getVideoDuration(entry) > 0;

  const task = async (entry) => {
    const videoStream = getVideoStream(entry)
    const {width, height} = videoStream
    const duration = getVideoDuration(entry)
    const logData = {video: {width, height, duration, size: entry.size}}
    log.debug(logData, `Starting video conversion of ${entry} (${width}x${height}, ${humanizeDuration(duration)}, ${humanizeBytes(entry.size)})`)

    const t0 = Date.now()
    const localFile = await storage.createLocalFile(entry, videoSuffix)
    return videoConverter(entry, localFile.file)
      .then(async () => {
        await localFile.commit()
        log.debug(t0, `Video conversion of ${entry} done`)
      })
      .catch(async err => {
        await localFile.release()
        log.warn(err, `Failed to convert video of ${entry}: ${err}`)
      })
  }

  return {
    test,
    task
  }
}

/**
 * @param {import('@home-gallery/types').TPluginManager} manager
 * @returns {import('@home-gallery/types').TExtractor}
 */
const videoPlugin = manager => ({
  name: 'video',
  phase: 'file',
  /**
   * @param {import('@home-gallery/types').TStorage} storage
   */
  async create(storage) {
    const config = manager.getConfig()
    const context = manager.getContext()
    const { ffmpegPath, ffprobePath } = context

    const options = {
      previewSize: 720,
      ext: 'mp4',
      ...config?.extractor?.video
    }
    const videoSuffix = `video-preview-${options.previewSize}.${options.ext}`
    const videoConverter = createVideoConverter(ffmpegPath, ffprobePath, options)

    return video(storage, videoConverter, videoSuffix)
  },
})

const plugin = toPlugin(videoPlugin, 'videoExtractor', ['metaExtractor'])

export default plugin