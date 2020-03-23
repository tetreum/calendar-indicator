#!/bin/bash
startPath=$(pwd)"/start.sh"
crontab -l | { cat; echo "@reboot $startPath"; } | crontab -
