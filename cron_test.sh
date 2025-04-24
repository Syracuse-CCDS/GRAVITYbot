#!/usr/bin/env bash
docker run -t --mount src=/opt/GRAVITYbot,target=/var/task,type=bind gravitybot python ./test/cron_test.py >> /opt/GRAVITYbot/cron_test.log 2>&1
