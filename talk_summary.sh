#!/usr/bin/env bash

#docker run -it --mount src=/opt/GRAVITYbot,target=/var/task,type=bind gravitybot python ./_src/__talk_summary_main__.py >> /opt/GRAVITYbot/jobs.log 2>&1
docker run --mount src=/opt/GRAVITYbot,target=/var/task,type=bind gravitybot python ./_src/__talk_summary_main__.py >> /opt/GRAVITYbot/jobs.log 2>&1
