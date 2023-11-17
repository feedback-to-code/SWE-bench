# Human Evaluation

on scorelab

have this repo and our fork of [cwa-server](https://github.com/feedback-to-code/cwa-server) cloned in your home dir on scorelab side-by-side.

in this repo run `conda env create file=environement.yml` and activate the env.

on cwa server repo run `gh repo set-default` and set our fork as default.


in this repo go to `evaluation` dir.
dvc pull the data

run `python3 human_eval.py`
