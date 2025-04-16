import { useEffect } from 'react';

import { useEventStore } from '../store/event-store'
import { getEvents, eventStream, eventBus } from '../api/ApiService';
import { useAppConfig } from '../utils/useAppConfig'

export const useLoadEvents = () => {
  const addEvents = useEventStore(state => state.addEvents);
  const appConfig = useAppConfig()

  useEffect(() => {
    const fetchEvents = () => getEvents()
      .then(events => addEvents(events?.data || []))
      .catch(e => {
        console.log(`Could not fetch intitial events: ${e}`);
      })
    eventBus.addEventListener('userAction', event => addEvents([event]))

    if (appConfig.disabledServerEvents) {
      console.log('Feature event stream is disabled')
    } else {
      eventStream()
    }

    fetchEvents()
  }, [])
}
