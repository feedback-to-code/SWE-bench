import sys, argparse, logging, os
import pandas as pd
from utils import *

from git import Repo

from git.exc import GitCommandError


# Gather our code in a main() function
def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    df = pd.read_csv("../data/cwa_server/evaluation.csv", index_col="id")

    if not os.path.isdir("./tmp/"):
        os.mkdir("./tmp/")

    repo = Repo.init("../../cwa-server/")
    git = repo.git

    git.fetch("origin")
    git.reset("--hard", "origin/main")
    git.switch("main")

    branch = "base_commit_branch"

    git.branch(branch)
    git.checkout(branch)

    failed_apply_prs = []
    for i, this in df.iterrows():
        logging.info("Creating patch files.")
        patch = this.prediction
        with open("./tmp/predicted.patch", "w") as diff_file:
            diff_file.write(patch)

        # go to base commit and apply patch
        logging.info(f"Resetting to base commit {this['base_commit']}")
        git.reset("--hard", this["base_commit"])

        try:
            git.apply("../SWE-bench/evaluation/tmp/predicted.patch", "--whitespace=fix", "-v", "--reject")
        except:
            failed_apply_prs.append(this.name)

    # delete
    git.checkout("main")
    git.branch("-D", branch)

    logging.info(f"Failed to apply patches for the following PRs: {failed_apply_prs}")
    logging.info("Done")


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Does a thing to some stuff.",
        epilog="As an alternative to the commandline, params can be placed in a file, one per line, and specified on the commandline like '%(prog)s @params.conf'.",
        fromfile_prefix_chars="@",
    )

    # parser.add_argument(
    #     "pr_number", help="pass number of PR to the program", metavar="pr_number"
    # )

    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    main(args, loglevel)
