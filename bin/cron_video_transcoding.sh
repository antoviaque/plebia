#!/bin/bash

MANAGE_CMD="`dirname $0`/../plebia/manage.py"

$MANAGE_CMD cron video_transcoding

