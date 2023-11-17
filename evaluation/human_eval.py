import sys, argparse, logging, os
import pandas as pd
from utils import *


# Gather our code in a main() function
def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)    

    logging.info(f"Choose unevaluated PR number from https://docs.google.com/spreadsheets/d/1KU2sSywl2VTK6JdVa73eC9r1UbhtMP9yaKb2gF5qmw0/edit?usp=sharing")
    logging.info(f"And document your findings there.")
    logging.info(f"Feel free to add new columns if you want to point towards something that does not fit in the existing columns.")
    pr_number = input("PR number: ")

    df = pd.read_csv("../fake_data/evaluation.csv", index_col="id")
    this = df.loc[int(pr_number)]

    logging.info("Creating patch files.")
    # create temporary patch files
    if not os.path.isdir("./tmp/"):
        os.mkdir("./tmp/")

    patch = this["patch"]
    with open("./tmp/real.patch", "w") as diff_file:
        diff_file.write(patch)

    patch = this["prediction"]
    with open("./tmp/predicted.patch", "w") as diff_file:
        diff_file.write(patch)

    # view create prs for viewing
    view_prs(
        this["base_commit"],
        "../SWE-bench/evaluation/tmp/real.patch",
        "../SWE-bench/evaluation/tmp/predicted.patch",
        "../../cwa-server/",
        pr_number,
    )

    logging.info(f"Original PR that also includes changed test cases.")
    logging.info(this.pr_link)
    logging.info(f"Original issue.")
    logging.info(this.issue_link)

    logging.info("Done with reviewing PRs? Mark as done in Google Sheet.")
    logging.info("'Enter' to continue.")
    input()

    # delete
    # TODO dont kown why up once instead of twice is sufficient
    cleanup_repo("../cwa-server/", pr_number)

    # delete patch files
    os.chdir("../SWE-bench/evaluation/")
    os.remove("./tmp/real.patch")
    os.remove("./tmp/predicted.patch")

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
