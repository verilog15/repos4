# File index option: journal

Tags: index, option, journal

* Add file "README.md" with content "# Readme"
* Add file "index.md" with content "# App"

## Create index with journal

* Create index with args "--journal abc"
* Exit code was "0"
* Index has "0" entries
* Journal "abc" has entries of "2" adds, "0" changes and "0" removals

## Create index on empty directory

* Remove file "README.md"
* Remove file "index.md"
* Create index
* Index has "0" entries

## Create journal on empty directory

* Remove file "README.md"
* Remove file "index.md"
* Create index with args "--journal abc"
* Index has "0" entries
* Journal "abc" has entries of "0" adds, "0" changes and "0" removals

## Create empty journal on unchanged directory

* Create index
* Create index with args "--journal abc"
* Index has "2" entries
* Journal "abc" has entries of "0" adds, "0" changes and "0" removals

## Add file

* Create index
* Add file "TODO.md" with content "# Todo"
* Create index with args "--journal abc"
* Journal "abc" has entries of "1" adds, "0" changes and "0" removals

## Add file keeps the file order

* Add file "d1/f1" with content "File 1"
* Add file "d2/f2" with content "File 2"
* Create index
* Add file "d1/.galleryignore" with content ""
* Create index with args "--journal abc"
* Apply journal "abc" with args "--keep"
* Index has file order "d2, d2/f2, d1, d1/.galleryignore, d1/f1, README.md, index.md"

## Remove file

* Create index
* Remove file "index.md"
* Update index with args "--journal abc"
* Journal "abc" has entries of "0" adds, "0" changes and "1" removals

## Rename file

* Create index
* Rename file "index.md" to "renamed.md"
* Update index with args "--journal abc"
* Journal "abc" has entries of "1" adds, "0" changes and "1" removals

## Overwrite file

* Create index
* Add file "index.md" with content "# TODO\n* Write tests"
* Create index with args "--journal abc"
* Journal "abc" has entries of "0" adds, "1" changes and "0" removals
* Journal "abc" entry "index.md" in "changes" has checksum "da5014965535f9703408cb61407112c05c3b79cb"
* Journal "abc" entry "index.md" in "changes" has prev checksum "9fc4ebc6fc993ebf08efb6d7a02a1fceda59e561"
* Apply journal "abc" with args "--keep"
* Index has entry "index.md" with checksum "da5014965535f9703408cb61407112c05c3b79cb"

## New checksum

* Create index with args "--no-checksum"
* Create index with args "--journal abc"
* Journal "abc" has entries of "0" adds, "2" changes and "0" removals
* Journal "abc" entry "README.md" in "changes" has checksum "cd0c0890b92695037143c16c5bee6d098bafcc76"
* Journal "abc" entry "index.md" in "changes" has checksum "9fc4ebc6fc993ebf08efb6d7a02a1fceda59e561"

## Apply journal

* Create index with args "--journal abc"
* Journal "abc" exists
* Apply journal "abc"
* Journal "abc" does not exist
* Index has "2" entries

## Apply journal fails

* Create index with args "--journal abc"
* Add file "index/journal/files.idx" as "config/files.idx" to root
* Apply journal "abc" fails
* Index has "1" entries

## Remove journal

* Create index with args "--journal abc"
* Journal "abc" exists
* Remove journal "abc"
* Journal "abc" does not exist
* Index has "0" entries
