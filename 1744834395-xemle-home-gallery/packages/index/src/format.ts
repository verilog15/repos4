import { humanizeBytes as humanize } from '@home-gallery/common'

const pad = (v: string | number, l: number, c = '0'): string => {
  v = '' + v
  l = l || v.length
  c = c || '0'
  while (v.length < l) {
    v = c + v
  }
  return v
}

export const percent = (current: number, total: number, precision = 1): string => (100 * current / total).toFixed(precision || 1) + '%'

export const bps = (bytes: number, startTime: number) => humanize(bytes / Math.max(0.001, (Date.now() - startTime) / 1000)) + '/s'

export const humanizeDuration = (duration: number): string => {
  if (duration <= 0) {
    return '0ms'
  } else if (duration < 800) {
    return duration.toFixed() + 'ms'
  } else if (duration < 3000) {
    return (duration / 1000).toFixed(2) + 's'
  } else if (duration < 20 * 1000) {
    return (duration / 1000).toFixed(1) + 's'
  } else if (duration < 60 * 1000) {
    return (duration / 1000).toFixed() + 's'
  } else if (duration < 60 * 60 * 1000) {
    const sec = +(duration / 1000).toFixed() % 60
    const min = (duration / 1000 / 60).toFixed()
    return `${pad(min, 2)}:${pad(sec, 2)}`
  } else {
    const sec = +(duration / 1000).toFixed() % 60
    const min = +(duration / 1000 / 60).toFixed() % 60
    const hours = (duration / 1000 / 60 / 60).toFixed()
    return `${hours}:${pad(min, 2)}:${pad(sec, 2)}`
  }
}

export const remainingTime = (startTime: number, current: number, total: number): number => {
  if (!total || total < current) {
    return 0
  }
  const elapsedTime = Math.max(0, Date.now() - startTime)
  const estimatedTotalTime = elapsedTime / (current / total)
  return estimatedTotalTime - elapsedTime
}
