import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

import Logger from '@home-gallery/logger'

const log = Logger('index.checksum');
import { humanizeBytes as humanize } from '@home-gallery/common';
import { bps, percent, remainingTime, humanizeDuration } from './format.js'
import { IIndexEntry } from './types.js';

const createByteProgressLog = (totalBytes: number, intervalMs: number) => {
  const startTime = Date.now()
  let last = startTime
  let lastWritten = 0
  let written = 0
  return data => {
    lastWritten += data.length
    const now = Date.now()
    if (now - last > intervalMs) {
      written += lastWritten
      log.info(`Processed ${humanize(written)} (${percent(written, totalBytes)}) with ${bps(lastWritten, last)}. Estimated remaining time is ${humanizeDuration(remainingTime(startTime, written, totalBytes))}`)
      lastWritten = 0
      last = now
    }
  }
}

const createSha1 = (filename, progress, cb) => {
  var input = fs.createReadStream(filename);
  var digest = crypto.createHash('sha1');

  const destroyStream = () => {
    input.destroy();
  }
  process.on('SIGINT', destroyStream)

  input.addListener('error', cb);
  input.addListener('data', data => digest.update(data));
  input.addListener('data', progress);
  input.addListener('close', () => {
    process.off('SIGINT', destroyStream);
    cb(null, digest.digest('hex'));
  });

};

export const checksum = (directory: string, entries: IIndexEntry[], checksumEntries: IIndexEntry[], sha1sumDate: string, cb: (err: Error | null, entries?: IIndexEntry[], interrupted?: boolean) => void) => {
  let interrupted = false;
  const t0 = Date.now();

  const updatedEntries: IIndexEntry[] = []
  if (!checksumEntries.length) {
    return cb(null, updatedEntries, interrupted);
  }

  const totalBytes = entries.reduce((all, entry) => all + entry.size, 0);
  const missingBytes = checksumEntries.reduce((all, entry) => all + entry.size, 0);
  let bytesCalculated = 0;
  log.info(`Calculating ids for ${checksumEntries.length} entries with ${humanize(missingBytes)} of total size ${humanize(totalBytes)} (${percent(missingBytes, totalBytes)})`);

  const gracefulShutdown = () => {
    if (!interrupted) {
      log.warn(`Graceful shutdown. Ids of ${humanize(bytesCalculated)} (${percent(bytesCalculated, missingBytes)}) were calculated, ${percent(totalBytes - missingBytes + bytesCalculated, totalBytes)} of ${humanize(totalBytes)} are done. Please be patient to avoid data loss!`);
      interrupted = true;
      cb(null, updatedEntries, interrupted);
    } else {
      log.warn(`Shutdown in progress. Please be patient to avoid data loss!`);
    }
  };
  process.on('SIGINT', gracefulShutdown);

  const progressLog = createByteProgressLog(missingBytes, 30 * 1000)

  const calculateAll = (entries, i, done) => {
    if (interrupted) {
      return;
    } else if (i >= entries.length) {
      return done(null);
    }
    const entry = entries[i++];
    const filename = path.join(directory, entry.filename);

    const t0 = Date.now()
    createSha1(filename, progressLog, (err, sha1sum) => {
      if (interrupted) {
        return;
      } else if (err) {
        log.warn(err, `Could not create checksum of ${filename}: ${err}. Continue.`)
        return calculateAll(entries, i, done);
      }
      entry.sha1sum = sha1sum;
      entry.sha1sumDate = sha1sumDate;
      updatedEntries.push(entry)

      bytesCalculated += entry.size;
      log.debug({duration: Date.now() - t0, bytes: entry.size}, `Calculated id ${sha1sum.substr(0, 7)}... for ${entry.filename} with ${humanize(entry.size)} (${bps(entry.size, t0)})`);
      calculateAll(entries, i, done);
    })
  }

  calculateAll(checksumEntries, 0, (err) => {
    process.off('SIGINT', gracefulShutdown);
    if (err) {
      return cb(err);
    }
    log.info(t0, `All ids of ${humanize(totalBytes)} are calculated. Calculated ids of ${humanize(bytesCalculated)} (${(100 * bytesCalculated / totalBytes).toFixed(1)}%)`);
    cb(null, updatedEntries, interrupted);
  });
}
