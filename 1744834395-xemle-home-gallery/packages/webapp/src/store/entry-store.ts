import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

import { Entry } from './entry'

export type Id2EntryMap = {[key: string]: Entry}

export interface EntryStore {
  id2Entries: Id2EntryMap
  allEntries: Entry[]
  entries: Entry[]

  reset: () => void
  addEntries: (entries: Entry[]) => void
  removeEntries: (entries: Entry[]) => void
  setEntries: (entries: Entry[]) => void
}

const slice = (set) => ({
  id2Entries: {},
  allEntries: [],
  entries: [],

  reset: () => set((state) => {
    return {
      ...state,
      id2Entries: {},
      allEntries: [],
      entries: []
    }
  }),
  addEntries: (entries: Entry[]) => set((state) => {
    if (!entries.length) {
      return state
    }
    const id2Entries: Id2EntryMap = entries.reduce((result, entry) => {
      result[entry.id] = entry
      return result
    }, {})
    const mergedId2Entries = {...state.id2Entries, ...id2Entries}
    const allEntries = Object.values(mergedId2Entries) as Entry[]

    // sort all entries by id. Entries should be search by binary search
    allEntries.sort((a: Entry, b: Entry) => a.id <= b.id ? -1 : 1)

    // SearchStore will listen to allEntries changes and updates entries
    return {
      ...state,
      id2Entries: mergedId2Entries,
      allEntries
    }
  }),
  removeEntries: (entries: Entry[]) => set((state) => {
    if (!entries.length) {
      return state
    }
    const entryIds = entries.map(entry => entry.id)
    const mapEntries = Object.entries(state.id2Entries).filter(([id]) => !entryIds.includes(id))

    const id2Entries = Object.fromEntries(mapEntries)
    const allEntries = mapEntries.map(([_, entry]) => entry) as Entry[]

    // sort all entries by id. Entries should be search by binary search
    allEntries.sort((a: Entry, b: Entry) => a.id <= b.id ? -1 : 1)

    // SearchStore will listen to allEntries changes and updates entries
    return {
      ...state,
      id2Entries,
      allEntries
    }
  }),

  setEntries: (entries: Entry[]) => set((state) => ({...state, entries}))
})

export const useEntryStore = create<
  EntryStore,
  [
    ["zustand/subscribeWithSelector", never]
  ]
>(subscribeWithSelector<EntryStore>(slice))
