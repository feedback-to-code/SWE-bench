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
        print("Could not apply predicted patch. Note this in Google Sheet.")
        patch = False

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
