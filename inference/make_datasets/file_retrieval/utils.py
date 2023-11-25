import os
from datasets import load_from_disk, load_dataset
from pathlib import Path
from git import Repo

import json
import numpy as np
from tqdm import tqdm


# Clones the repo and does checkout to the base commit
def clone_repo(user, repo_name, commit_sha):
    repository_url = f'https://github.com/{user}/{repo_name}.git'
    destination_path = f'{user}__{repo_name}'
    if not Path(destination_path).exists():
        Repo.clone_from(repository_url, destination_path)
    repo = Repo(destination_path)
    repo.git.checkout(commit_sha)
    return repo


def get_code_from_file(file_path):
    with open(file_path, "r") as f:
        return f.read()
    

# get all the code files as strings from the repo
def get_code_files(user, repo_name):
    file_contents = []
    # iterate over every file in the feedback-to-code__cwa-server folder
    for root, dirs, files in os.walk(f"{user}__{repo_name}"):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                code_content = get_code_from_file(file_path)
            except:
                continue
            file_content = f"FileName:\n{file_path}\nCode:\n{code_content}"
            # very rough length check
            if len(file_content) > 15000:
                continue
            file_contents.append(file_content)
            # ToDo: Add file_path to the start of file contents and split file contents up into chunks
    return file_contents


def save_dict_to_json(dict, file_name):
    current_directory = os.getcwd()
    with open(f"{current_directory}/{file_name}.json", "w") as f:
        json.dump(dict, f, indent=4)


def get_dataset_from_huggingface(dataset_name_or_path):
    # if Path(dataset_name_or_path).exists():
    #     dataset = load_from_disk(dataset_name_or_path)
    #     dataset_name = os.path.basename(dataset_name_or_path)
    # else:
    dataset = load_dataset(dataset_name_or_path)
    dataset_name = dataset_name_or_path.replace("/", "__")
    return dataset, dataset_name