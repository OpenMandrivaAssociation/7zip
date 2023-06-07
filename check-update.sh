#!/bin/sh
curl -s https://www.7-zip.org/download.html |grep 'Download 7-Zip' |grep -viE '(alpha|beta|rc)' |head -n1 |sed -e 's,.*Download 7-Zip ,,' |cut -d' ' -f1
