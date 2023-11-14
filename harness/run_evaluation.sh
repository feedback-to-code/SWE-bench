#!/bin/bash
python run_evaluation.py \
    --predictions_path "../data/cwa_server/predictions.json" \
    --swe_bench_tasks "../data/cwa_server/cwa-server-task-instances.json" \
    --log_dir "./log_dir" \
    --testbed "./testbed" \
    --verbose
