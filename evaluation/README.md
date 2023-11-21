# Human Evaluation

on scorelab

first you have to install miniconda https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html
see https://docs.conda.io/projects/miniconda/en/latest/#quick-command-line-install for instructions

have THIS repo and our fork of [cwa-server](https://github.com/feedback-to-code/cwa-server) cloned in your home dir on scorelab side-by-side.

in THIS repo run `conda env create file=environment.yml` and activate the env (`conda activate swe-bench`).
If this doesn't work, you might want to try `conda env create -f environment.yml` and then activate the env.

Run `gh auth login` in order to set up the GitHub CLI
in cwa server repo run `gh repo set-default` and set our fork as default.

in THIS repo go to `evaluation` dir.

run `python3 human_eval.py`

From here on follow what is written in the terminal and read carefully :)

## The Commands you need to run to do all this
- ssh vorname.nachname@delab.i.hpi.de (enter hpi password)
- git clone https://github.com/feedback-to-code/cwa-server.git
- git clone https://github.com/feedback-to-code/SWE-bench.git
- mkdir -p ~/miniconda3
- wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
- bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
- rm -rf ~/miniconda3/miniconda.sh
- ~/miniconda3/bin/conda init bash
- exec bash
- cd SWE-bench/
- conda env create -f environment.yml
- conda activate swe-bench
- cd ..
- cd cwa-server/
- gh auth login (login)
- gh repo set-default (choose feedback-to-code/cwa-server)
- cd ..
- cd SWE-bench/
- cd evaluation/
- python3 human_eval.py
