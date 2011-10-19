#!/bin/bash

BIN_DIR="`dirname $0`"

for cron in torrent_search torrent_download package_management video_transcoding contentdb_update ; do
    echo "Running $BIN_DIR/cron_$cron.sh ..."
    $BIN_DIR/cron_$cron.sh
done

