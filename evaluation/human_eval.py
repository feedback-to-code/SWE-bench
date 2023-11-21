import sys, argparse, logging, os
import pandas as pd
from utils import *


# Gather our code in a main() function
def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)    

    while not os.path.isdir("SWE-bench/"):
        os.chdir("../")
    dir = os.getcwd()
    cwa_server_path = dir + "/cwa-server/"
    swe_bench_path = dir + "/SWE-bench"


    logging.info(f"Choose unevaluated PR number from https://docs.google.com/spreadsheets/d/1KU2sSywl2VTK6JdVa73eC9r1UbhtMP9yaKb2gF5qmw0/edit?usp=sharing")
    logging.info(f"And document your findings there.")
    logging.info(f"When documenting try to align with the format other people used.")
    logging.info(f"Feel free to add new columns if you want to point towards something that does not fit in the existing columns.")
    logging.info(f"If this run fails or gets interrupted, run it again with the same PR number for a proper clean-up.")
    pr_number = input("PR number: ")

    try:
        df = pd.read_csv(f"{swe_bench_path}/fake_data/evaluation.csv", index_col="id")
        this = df.loc[int(pr_number)]

        logging.info("Creating patch files.")
        # create temporary patch files
        if not os.path.isdir(f"{swe_bench_path}/evaluation/tmp/"):
            os.mkdir(f"{swe_bench_path}/evaluation/tmp/")

        patch = this["patch"]
        with open(f"{swe_bench_path}/evaluation/tmp/real.patch", "w") as diff_file:
            diff_file.write(patch)

        patch = this["prediction"]
        with open(f"{swe_bench_path}/evaluation/tmp/predicted.patch", "w") as diff_file:
            diff_file.write(patch)

        # view create prs for viewing
        view_prs(
            this["base_commit"],
            f"{swe_bench_path}/evaluation/tmp/real.patch",
            f"{swe_bench_path}/SWE-bench/evaluation/tmp/predicted.patch",
            cwa_server_path,
            pr_number,
        )

        logging.info(f"Original PR that also includes changed test cases.")
        logging.info(this.pr_link)
        logging.info(f"Original issue.")
        logging.info(this.issue_link)
        logging.info(f"You are at base commit {this.base_commit}.")

        logging.info("Done with reviewing PRs? Mark as done in Google Sheet.")
        logging.info("'Enter' to continue.")
        input()

        # delete
        cleanup_repo(cwa_server_path, pr_number)

        # delete patch files
        os.remove(f"{swe_bench_path}/evaluation/tmp/real.patch")
        os.remove(f"{swe_bench_path}/evaluation/tmp/predicted.patch")

        logging.info("Done")
    except Exception as e:
        logging.error(f"Something went wrong. {e}")
        cleanup_repo(cwa_server_path, pr_number)


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
