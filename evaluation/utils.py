import re

from git import Repo

from git.exc import GitCommandError
import sys
import os


def find_files(text):
    files = []
    regex = "\[start of (.+?)\]"
    m = re.search(regex, text)
    while True:
        files.append(m.group(1))
        text = text.replace(m.group(0), "")
        m = re.search(regex, text)
        if m is None:
            break
    return files


def view_prs(
    base_commit: str,
    real_patch_path: str,
    predicted_patch_path: str,
    repo_path: str,
    pr_number: int,
):
    print("Creating PRs...")

    viewing_branch = f"viewing_branch_{pr_number}"
    real_patch_branch = f"real_patch_branch_{pr_number}"
    pred_patch_branch = f"pred_patch_branch_{pr_number}"

    repo = Repo.init(repo_path)
    git = repo.git

    # go to main branch
    git.fetch("origin")
    git.reset("--hard", "origin/main")
    git.switch("main")

    # go to the base commit and create all needed branches from it
    git.checkout(base_commit)
    git.branch(viewing_branch)
    git.branch(real_patch_branch)
    git.branch(pred_patch_branch)
    
    # treat all three branches
    git.switch(viewing_branch)
    git.push("--set-upstream", "origin", viewing_branch)

    # go to branches to create a pr from
    # apply code changes
    git.switch(real_patch_branch)
    git.apply(real_patch_path, "--whitespace=fix")
    git.commit("--all", "--message=applied real patch")
    git.push("--set-upstream", "origin", real_patch_branch)
    
    patch = True
    try:
        git.switch(pred_patch_branch)
        git.apply(predicted_patch_path, "--whitespace=fix")
        git.commit("--all", "--message=apply predicted patch")
        git.push("--set-upstream", "origin", pred_patch_branch)
    except GitCommandError as e:
        print(e)
        print("\nCould not apply predicted patch. Note this in Google Sheet.")
        print("We want to find out why it failed to apply. For this do the following:")
        print(f"Go into {repo_path}. You should be on the {viewing_branch} branch.")
        print("Apply the patch manually running:")
        print(f"git apply {predicted_patch_path} --whitespace=fix --reject --verbose")
        print("This will show you the conflicts. It is possible that some hunks can be applied.")
        print("Take a look at the hunks that can/ cannot be applied - note interesting finding in Google Sheet.")
        print("What are the problems why it cannot be applied")
        print("Try to modify the patch file so that it can be applied.")
        print("This might be of interest if there is just a tiny problem with some of the hunks.")
        print("If you were successful fully applying the patch, put the code of your")
        print("modified patch file into the Google Sheet column modified_patch.")
        print("Take care when pasting the patch it format is like this")
        print("that it can be applied when reading from this table.")
        print("At the end, git stash and go back to the evaluation run.\n")

        patch = False

    git.switch(viewing_branch)
    os.chdir(repo_path)

    # create prs
    if patch:
        try:        
            os.system(
                f'gh pr create --title "view real patch" --body "." --base {viewing_branch} --head {real_patch_branch}'
            )
            os.system(
                f'gh pr create --title "view predicted patch" --body "." --base {viewing_branch} --head {pred_patch_branch}'
            )

            print(f"\nSuccessfully created PRs! See them on github.")
            print(f"Branch patches should be merged to.")
            print(f"https://github.com/feedback-to-code/cwa-server/tree/{viewing_branch}")
            print(f"You can find links to the patch PRs above.\n")
        except:
            print("Could not create PRs.")



def cleanup_repo(repo_path: str, pr_number: int):
    viewing_branch = f"viewing_branch_{pr_number}"
    real_patch_branch = f"real_patch_branch_{pr_number}"
    pred_patch_branch = f"pred_patch_branch_{pr_number}"

    repo = Repo.init(repo_path)
    git = repo.git

    # delete branches on github - closes prs automatically
    git.push("origin", "--delete", viewing_branch)
    git.push("origin", "--delete", real_patch_branch)
    try:
        git.push("origin", "--delete", pred_patch_branch)
    except:
        print("Could not delete pred_patch_branch remote. It probably does not exist.")

    # delete branches locally
    git.checkout("main")
    git.branch("-D", viewing_branch)
    git.branch("-D", real_patch_branch)
    try:
        git.branch("-D", pred_patch_branch)
    except:
        print("Could not delete pred_patch_branch locally. It probably does not exist.")

    print("Successfully cleaned up!")
