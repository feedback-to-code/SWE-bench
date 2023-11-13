#!/bin/bash

python get_tasks_pipeline.py \
    --repos 'corona-warn-app/cwa-server'\
    --path_prs './prs' \
    --path_tasks './tasks'
