# FileRenamer

MP3's get named with special characters which breaks on USB so want to run a program over a directory to remove/replace non alphanumeric characters that stopped the file from copying over.

## Getting started

```
git clone git@github.com:TomMcCallum/filerenamer.git
python filerename.py -c <config> --force <target>
```


## Arguments

* target - this can be an mp3 file, an m3u file or a directory.  If an m3u file is give both the name of the m3u file and the contents are checked.  Lines starting with #EXT are ignored.  If a directory is given then all subdirectories, m3u and mp3 files are checked as well.
* config - a json format file with rename and replace keys
* force - by default no changes are made, only when ```--force``` given will changes be made.  Will output all transformations performed to stdout.

## Dependencies

Should not need additional dependencies as only requires these installed packages:

```
import os
import sys
import json
import shutil
```