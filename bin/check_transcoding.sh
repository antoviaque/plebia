#!/bin/bash

ps auxwww|grep "$1" |grep ffmpeg >/dev/null

