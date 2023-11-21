import re

from git import Repo
import git

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
    branches = [viewing_branch, real_patch_branch, pred_patch_branch]

    repo = Repo.init(repo_path)
    git = repo.git

    # go to main branch
    git.fetch("origin")
    git.reset("--hard", "origin/main")
    git.switch("main")

    # sanity clean-ups
    clean_local_branches(git)
    clean_remote_branches(git, branches)

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
    git.add(all=True)
    git.commit("--all", "--message=applied real patch")
    git.push("--set-upstream", "origin", real_patch_branch)
    
    patch = True
    try:
        git.switch(pred_patch_branch)
        git.apply(predicted_patch_path, "--whitespace=fix")
        git.add(all=True)
        git.commit("--all", "--message=apply predicted patch")
        git.push("--set-upstream", "origin", pred_patch_branch)
    except GitCommandError as e:
        print(e)
        print("\nCould not apply predicted patch. Note this in Google Sheet.")
        print("We want to find out why it failed to apply. For this do the following:")
        print(f"Go into {repo_path}. You should be on the {viewing_branch} branch.")
        print("Apply the patch manually running:\n")
        print(f"git apply {predicted_patch_path} --whitespace=fix --reject --verbose")
        print("\nThis will show you the conflicts. It is possible that some hunks can be applied.")
        print("Take a look at the hunks that can/ cannot be applied - note interesting finding in Google Sheet.")
        print("What are the problems why it cannot be applied")
        print("Try to modify the patch file so that it can be applied. Delete/ change some hunks, lines, etc.")
        print("This might be of interest if there is just a tiny problem with some of the hunks.")
        print("If you were successful modifying the patch so that it can by applied, put the code of your")
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

def clean_local_branches(git: git.cmd.Git):
    # sanity clean-up of unneeded local branches
    git.checkout("main")
    local_branches = git.branch()
    local_branches = [x.strip() for x in local_branches.split("\n")]
    local_branches.remove("* main")
    for branch in local_branches:
        git.branch("-D", branch)
    print("Cleaned up local branches.")

def clean_remote_branches(git: git.cmd.Git, branches_to_delete: list):
    # sanity clean-up of unneeded remote branches
    remote_branches = git.branch("-r")
    remote_branches = [x.strip() for x in remote_branches.split("\n")]
    for branch in branches_to_delete:
        if f"origin/{branch}" in remote_branches:
            git.push("origin", "--delete", branch)
    print("Cleaned up remote branches.")


def cleanup_repo(repo_path: str, pr_number: int):
    viewing_branch = f"viewing_branch_{pr_number}"
    real_patch_branch = f"real_patch_branch_{pr_number}"
    pred_patch_branch = f"pred_patch_branch_{pr_number}"
    branches = [viewing_branch, real_patch_branch, pred_patch_branch]

    repo = Repo.init(repo_path)
    git = repo.git

    clean_remote_branches(git, branches)
    clean_local_branches(git)

    print("Successfully cleaned up!")

    

    
