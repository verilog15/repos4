import { Transform } from 'stream'
import { createGzip } from 'zlib'

import { through, compose, createAtomicWriteStream } from '@home-gallery/stream'
import Logger from '@home-gallery/logger'

import { getDatabaseFileType } from './migrate.js'

const log = Logger('database.writeStream')

/**
 * @param {string} filename
 * @param {Date} [created]
 * @returns {Promise<Transform[]>}
 */
export const createWriteStream = async (filename, created = new Date()) => {
  const fileStream = await createAtomicWriteStream(filename)
  const databaseFileType = getDatabaseFileType()

  return compose(
    createStringifyEntry(databaseFileType, created),
    createGzip(),
    fileStream,
    new Transform({
      flush(cb) {
        log.debug(`Database written to ${filename}`)
        cb()
      }
    })
  )
}

/**
 * @param {Date} created
 * @returns {Transform}
 */
export const createStringifyEntry = (databaseFileType, created = new Date()) => {
  let isFirstEntry = true

  const headerJson = JSON.stringify({
    type: databaseFileType.toString(),
    created: created.toISOString(),
    data: []
  })

  const stream = through(function(entry, enc, cb) {
    let data = ''
    if (isFirstEntry) {
      data += headerJson.substring(0, headerJson.length - 2)
      isFirstEntry = false
    } else {
      data += ','
    }

    data += JSON.stringify(entry)
    cb(null, data)
  }, function(cb) {
    const data = isFirstEntry ? headerJson : "]}"
    cb(null, data)
  })

  return stream
}
