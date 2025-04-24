#!/usr/bin/env bash

#docker run -it --mount src=/opt/GRAVITYbot,target=/var/task,type=bind gravitybot python ./_src/__alog_summary_main__.py >> /opt/GRAVITYbot/jobs.log 2>&1
docker run -t --mount src=/opt/GRAVITYbot,target=/var/task,type=bind gravitybot python ./_src/__alog_summary_main__.py >> /opt/GRAVITYbot/jobs.log 2>&1
