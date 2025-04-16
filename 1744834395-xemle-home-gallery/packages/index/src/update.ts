import Logger from '@home-gallery/logger'

const log = Logger('index.update');

import { mergeIndex }  from './merge.js';
import { IIndexChanges, IIndexEntry, IIndexEntryMatcherFn } from './types.js';

function toMap<T>(values: T[], keyFn: (item: T) => string): Record<string, T> {
  return values.reduce((result, value) => {
    const key = keyFn(value)
    if (!key) {
      log.info(`Could not find key for ${value}`)
    } else {
      result[key] = value
    }
    return result
  }, {})
}

const hasNoChanges = (onlyFileKeys: string[], onlyFsKeys: string[], changedKeys: string[]) => !onlyFileKeys.length && !onlyFsKeys.length && !changedKeys.length

const initialChanges = (entries: IIndexEntry[]): IIndexChanges => {
  return {
    adds: entries,
    changes: [],
    removes: []
  }
}

export const updateIndex = async (fileEntries: IIndexEntry[], fsEntries: IIndexEntry[], matcherFn: IIndexEntryMatcherFn): Promise<[IIndexEntry[], IIndexChanges]> => {
  const t0 = Date.now();
  if (!fileEntries.length) {
    log.info(`Initiate index with ${fsEntries.length} entries`);
    return [fsEntries, initialChanges(fsEntries)];
  }

  const fileEntryMap = toMap(fileEntries, e => e.filename);
  const fsEntryMap = toMap(fsEntries, e => e.filename);
  const fileKeys = Object.keys(fileEntryMap);
  const fsKeys = Object.keys(fsEntryMap);

  const onlyFileKeys = fileKeys.filter(key => !fsEntryMap[key]);
  const onlyFsKeys = fsKeys.filter(key => !fileEntryMap[key]);
  const commonKeys = fileKeys.filter(key => fsEntryMap[key]);

  const [ commonEntryMap, changedKeys ] = mergeIndex(fileEntryMap, fsEntryMap, commonKeys, matcherFn);

  if (hasNoChanges(onlyFileKeys, onlyFsKeys, changedKeys)) {
    log.info(t0, `No changes found`);
    return [fileEntries, initialChanges([])];
  }

  const updatedEntryKeys = commonKeys.concat(onlyFsKeys);
  const updatedEntries = updatedEntryKeys.map(key => commonEntryMap[key] || fsEntryMap[key]);

  const changes = {
    adds: onlyFsKeys.map(key => fsEntryMap[key]),
    changes: changedKeys.map(key => ({...fsEntryMap[key], sha1sum: '', prevSha1sum: fileEntryMap[key].sha1sum || ''})),
    removes: onlyFileKeys.map(key => fileEntryMap[key])
  }

  log.info(t0, `Index merged of ${updatedEntryKeys.length} entries (${onlyFsKeys.length} added, ${changedKeys.length} changed, ${onlyFileKeys.length} deleted)`)

  const logChanges = {
    adds: onlyFileKeys,
    changes: changedKeys,
    removes: onlyFileKeys
  }
  const changeLines = [
    ...onlyFsKeys.map(f => `A ${f}`),
    ...changedKeys.map(f => `C ${f}`),
    ...onlyFileKeys.map(f => `D ${f}`)
  ]
  log.info(logChanges, `Changes:\n\t${changeLines.join('\n\t')}`)

  return [updatedEntries, changes]
}
