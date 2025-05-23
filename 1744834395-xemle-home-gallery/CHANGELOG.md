# Changelog of HomeGallery

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- server: Add option flag --import-sources

### Changed

- webapp: Load offline db in chronlogical order, latest first
- webapp: Improve offline db performance

### Fixed

- extractor: Fix video extraction for webm
- server: Fix download original files with whitespace

## [1.19.0] - 2025-01-05

### Added

- webapp: Feature flag for sources to download original files

### Changed

- index: Apply file index journal after successful database update

### Fixed

- server: Fix user on server log
- storage: Log error on storage purge

## [1.18.0] - 2024-09-24

### Added

- webapp: Add toggle for face and object annotations
- server: Add option prefix
- webapp: Support IPTC description

### Changed

- server: Reduce log levels of request logs

### Fixed

- webapp: Fix tag wrap in detail view
- query: Fix location alias
- webapp: Fix street/road search link
- webapp: Fix similarity search
- server: Fix page reload with base path
- webapp: Fix browser based router with base path

## [1.17.0] - 2024-09-15

### Added

- webapp: Add dynamic load of plugins
- cli: Add build version
- extractor: Add support for avif images

### Changed

- plugin: Add register for extensions
- plugin: Deprecate ModuleFactory

### Fixed

- server: Fix base path with multiple path segements
- webapp: Fix tag list with different tag cases
- plugin: Fix plugin module load on windows
- cli: Fix execution on windows
- bundle: Fix binary tmp dir with snapshot
- extractor: Fix image resizer for all existing previews

## [1.16.1] - 2024-08-10

### Fixed

- server: Fix user filter for initial app state

## [1.16.0] - 2024-08-09

### Added

- server: Add user based filter to customize database access
- plugin: Add query plugin (server side)
- server: Add SHA256-salted password schema
- plugin: Initial plugin manager (experimental)
- cli: Only import changed sources in watch mode
- database: Use stream based database reader and writer

### Changed

- database: Stream based database build to reduce resouces
- database: Rewrite database migration handling
- database: Use stream based database reader and writer
- Use ESM instead of CommonJS

### Fixed

- server: Fix arguments to handle database read errors
- extractor: Fix vips thumbnail creation on relative storage dir
- server: Fix env for missing config file arg

## [1.15.1] - 2024-06-15

### Added

- cli: Read settings from config for most commands
- database: Read settings from config

### Changed

- docker: Disable armv6 and armv7 builds due github build failures

### Fixed

- docker: Raise node version v20
- webapp: No browser history for singe media navigation
- webapp: search tags with blanks in Detail

## [1.15.0] - 2024-01-27

### Changed

- webapp: Rewrite css using tailwindcss

## [1.14.6] - 2024-01-04

### Fixed

- database: Fix dimensions on videos

## [1.14.5] - 2023-12-20

### Changed

- index: Follow symbolic links

### Fixed

- docker: Set default settings of api server for SoC devices
- cli: Env overwrites api server config settings

## [1.14.4] - 2023-12-17

### Fixed

- server: Fix cache header for static public files
- extractor: Fail gracefully on missing perl dependency

## [1.14.3] - 2023-12-12

### Fixed

- extractor: Fix debugging with concurrent one
- cli: Fix interactive debug tasks

## [1.14.2] - 2023-12-02

### Fixed

- webapp: Disable features by query parameter
- server: Add configuration to disable webapp features

## [1.14.1] - 2023-11-20

### Fixed

- cli: Fix interactive import tasks

## [1.14.0] - 2023-11-18

### Added

- webapp: Add offline database via IndexedDB

### Changed

- extractor: Set video file extension for custom ffmpeg args
- Update node LTS to v20

### Fixed

- query: Fix random sort order

## [1.13.3] - 2023-11-07

### Fixed

- common: Detect raw image files from Gopro, Nicon, Olympus, Samsung, Sony
- extractor: Custom image preview size for heic files
- cli: Keep config env for run import

## [1.13.2] - 2023-10-15

### Fixed

- webapp: Fix preview size quality by devicePixelRatio
- fetch: Fix reconnect on unknown host

## [1.13.1] - 2023-09-30

### Fixed

- webapp: search only for tags on tags-page

## [1.13.0] - 2023-09-22

### Added

- export: Export metadata to xmp sidecar files
- database: Add `remove` subcommand

### Fixed

- index: Fix passing existing files in file limit filter
- cli: Fix config default value of sources

## [1.12.2] - 2023-08-17

### Fixed

- extractor: Fix api server timeout

## [1.12.1] - 2023-08-06

### Fixed

- cast: Fix fetching remote database
- extractor: Fix support for webp image format

## [1.12.0] - 2023-08-05

### Added

- fetch: Add `--force-download` and `--download-all` options

### Fixed

- bundle: Fix binary app bundling

## [1.11.1] - 2023-08-03

### Fixed

- extractor: Fix native ffmpeg and ffprobe commands for docker

## [1.11.0] - 2023-08-03

### Added

- fetch: Add watch option
- extractor: Optional disable api detections
- extractor: Add custom ffmpeg args
- extractor: Add custom preview video size
- extractor: Add custom preview image sizes

### Changed

- extractor: Upgrade sharp dependency for image resizer
- logger: Add time prefix (martadinata666)

### Fixed

- index: Fix read stream for empty index
- webapp: Fix icon paths of PWA webmanifest
- webapp: Fix database load on bootstrap
- cli: Fix find config for undefined HOME env
- extractor: Fix preview video size of portrait videos
- database: Fix video rotation
- database: Fix video duration

## [1.10.0] - 2023-06-13

### Added

- server: Watch sources while running the server
- cli: Add json format for console logger
- cli: Add watch mode of run import command

### Changed

- bundle: Rewrite dependency resolver
- logger: Log ISO timestamp instead of epoch
- cli: Batch and increase file sizes on initial import
- index: Keep known files on max size filter

### Fixed

- webapp: Fix vanished media in single view
- database: Fix preview paths on Windows hosts
- server: Fix database watcher
- cli: Honor custom server port in `gallery.config.yml`

## [1.9.0] - 2023-01-11

### Added

- webapp: Add higher row height for portait images
- webapp: Add tag dialog for single media
- webapp: Add autocomplete to tag dialog

### Changed

- server: Use gallery config instead of cli args

### Fixed

- query: Fix query with duplicated entry ids
- events: Fix apply events with duplicated entry ids
- webapp: Fix location links from media detail

## [1.8.5] - 2022-12-21

### Fixed

- webapp: Fix previews for smaller images
- webapp: Show geo nav if coordinate is available
- webapp: Keep search after initial events

## [1.8.4] - 2022-12-06

### Fixed

- index: Fix order of index and journal
- index: Fix exclude-if-present option
- cli: Fix interactive rebuild database task
- database: Fix log calls
- webapp: Fix swipe on videos
- webapp: Fix visibility of video time in media stream
- extractor: Create previews of JPE and WEBP image files

## [1.8.3] - 2022-12-01

### Fixed

- docker: Fix server webapp files
- webapp: Fix adding tags
- index: Fix small files filter with limit filter
- config: Allow simple source definition

## [1.8.2] - 2022-11-20

### Fixed

- Fix binary build

## [1.8.1] - 2022-11-20

### Fixed

- Fix docker and binary build with pnpm

## [1.8.0] - 2022-11-20

### Added

- cli: Add storage purge command
- export: Add --edit option to enable edit menu
- fetch: Add --delete option to remove non existing local files
- server: Add base path option

### Changed

- export: Disable edit menu by default. Use --edit to enable it
- webapp: Upgrade react router
- Replace lerna by pnpm to build the project
- Upgrade to node 18
- webapp: Upgrade react to 18.x
- webapp: Replace easy-peasy by zustand

### Fixed

- webapp: Fix toggle of selected media
- webapp: Fix single view for not yet loaded media
- webapp: Fix pre-loading of previews

## [1.7.0] - 2022-11-02

### Added

- extractor: Log warning if public api server is used
- webapp: Add map feature
- index: Add filter option for maximum file size
- webapp: Improve search by subfolder
- webapp: Improve parallel fetch of database

### Fixed

- webapp: Fix timeline scrollbar on iOS (partially)
- extractor: Fix video log for docker on ARM
- extractor: Fix video poster to first frame
- database: Use geo locations from sidecars
- webapp: Fix updates of year view while loading

## [1.6.1] - 2022-08-13

### Fixed

- webapp: Fix 404 empty events response

## [1.6.0] - 2022-08-03

### Added

- webapp: Add timeline scrollbar
- webapp: Add optional remote console for debugging purposes

## [1.5.0] - 2022-07-15

### Added

- database: Honor date from meta sidecars
- webapp: Use shorten id in links against history attacks
- webapp: Improve database chunk size adjustment based on response times
- webapp: Improve caching with hashed asset filenames
- webapp: Add image and video amount to year list
- webapp: Improve UI by fetching data in separate web worker
- extractor: Improve low powered api server with timout and concurrent parameter

### Fixed

- webapp: Fix preview sizes in stream
- bin: Raise node version to v16.16.0 to general fix security issues
- webapp: Fix data mapping for initial state
- database: Speedup id grouping
- fetch: Fix query with polluted text cache
- export: Fix query with polluted text cache
- webapp: Fix relative resources from base URI
- webapp: Fix previews of smaller images
- docker: Fix docker-compose setup

## [1.4.1] - 2022-03-26

### Fixed

- docker: Fix arm image build

## [1.4.0] - 2022-03-26

This release adds tags from XMP sidecar files, enhances the media search
capabilities, adds support to use native commands like ffmpeg, extracts preview
files from RAW images and adds support to HEIC files (from iphones).

### Added

- docker: Support arm docker images
- bundle: Add all-generic bundle
- cli: Configuration for max memory value for database creation
- extractor: Create only smaller preview images than the source
- extractor: Option to use native system executables like vipsthumbnail or ffmpeg
- extractor: Add support for heic/heif image format
- extractor: Extract embedded previews from raw files
- query: Add cmp, (all) in list and range to common properties
- query: Allow capitalized keywords
- database: Add entry groups
- database: Add updated timestamp
- database: Support IPTC keywords as tags
- index: Improve journal for sidecar changes
- server: Add optional basic authentication of users and ip whitelists
- webapp: Add a tab to list tags (by biolds)
- extractor: Add option for geo address server
- extractor: Add error threshold for api calls
- cast: Add reverse option

### Changed

- Default node version is v16 (Gallium)
- extractor: Reduce log levels. Use debug log level for details
- cast: Set default order is by date oldest first

### Fixed

- cli: Fix update with source selection
- extractor: Fix resizing to squared boundary size
- query: Fix query expression with keyword prefix like india or andrea
- extractor: Except buggy Samsung images (by psdimon)
- query: Fix query expressions with parenthesis
- database: Unify city geo information from hamlet, village, town
- fetch: Improve error handling for events

## [1.3.0] - 2021-08-27

### Added

- Add cast cli for a Chromecast-enabled slide show
- server: Apply events on database load
- server: Allow query parameter for database api
- Add fetch command to fetch and merge a remote gallery

### Changed

- Use `/api/database.json` instead of `/api/database`
- Use `/api/events.json` instead of `/api/events`

### Fixed

- database: Handle incomplete geo data
- index: Fix graceful abort by user (ctrl-c)

## [1.2.2] - 2021-08-18

### Fixed

- Fix test execution on parallel streams
- Fix logger colors for terminals with color level 1 (16 colors)
- index: Fix error handling on checksum calculation

## [1.2.1] - 2021-08-08

### Fixed

- Fix cli logger call

## [1.2.0] - 2021-08-06

### Added

- Add option to open browser on server start
- Add logger with console and file logger
- Add quick search links on some media meta data
- Add keyboard shortcuts to single view
- Add end to end tests
- Add file index journal
- Speedup incemental database updates via file index journal

### Fixed

- export: Fix webapp copy for export
- index: Fix checksum option. Use `--no-checksum` to disable it

## [1.1.0] - 2021-06-22

This release improves the installation options, the initial usage
and adds valuable configuration options.
It offers official docker images `xemle/home-gallery` and `xemle/home-gallery-api-server`
and better local setup through docker-compose.

### Added

- Add initial `docker-compose.yml`
- Add incremental import with database reload support
- Add run cli command to init config, start the server or source import directly
- config: Add `matcher` for index file matcher
- config: Add `geoAddressLanguage` for geo code reverse lookup language
- extractor: Print video progress
- extractor: Add `--concurrency`, `--skip` and `--limit` parameter for issue identifications
- server: Wait for database file if not exist
- index: Add `--add-limits` parameter

### Changed

- cli: Extract and unify separate cli package
- index: Calculate file checksum by default. Use `--no-checksum` to disable it
- index: Changed sort order. Initial import imports latest dirs first
- docker: Use docker builder and app bundle
- database: Add atomic write for database

### Fixed

- config: Fix example parameter `apiServer`
- server: Fix database cache middleware
- index: Fix incremental import with multiple indices

## [1.0.1] - 2021-05-20

Bugfix release

### Fixed

- webapp: Fix empty search query
- cli: Fix source directories with whitespaces

## [1.0.0] - 2021-05-15

Initial release of 1.0.0
