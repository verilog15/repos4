import { through } from '@home-gallery/stream'
import { sidecars } from '@home-gallery/common'

export const groupSidecarFiles = () => {
  return through(function (entries, enc, cb) {
    this.push(sidecars.groupSidecarFiles(entries))

    cb()
  })
}
