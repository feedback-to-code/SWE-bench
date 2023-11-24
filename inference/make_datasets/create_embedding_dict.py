import chromadb
import os
from datasets import load_from_disk, load_dataset
from pathlib import Path

import logging

from github import Github
from git import Repo
import base64

from langchain.embeddings import CacheBackedEmbeddings, OpenAIEmbeddings
from langchain.storage import (
    InMemoryStore,
    LocalFileStore,
    RedisStore,
    UpstashRedisStore,
)
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

import json
import numpy as np
from tqdm import tqdm

def get_code_from_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

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
            file_content = f"FileName:\n{file}\nCode:\n{code_content}"
            # very rough length check
            if len(file_content) > 15000:
                continue
            file_contents.append(file_content)
            # ToDo: Add file_path to the start of file contents and split file contents up into chunks
    return file_contents


# Clones the repo and does checkout to the base commit
def clone_repo(user, repo_name, commit_sha):
    repository_url = f'https://github.com/{user}/{repo_name}.git'
    destination_path = f'{user}__{repo_name}'
    # Check if destination path already exists
    if not Path(destination_path).exists():
        Repo.clone_from(repository_url, destination_path)
    # checkout to commit_sha
    repo = Repo(destination_path)
    repo.git.checkout(commit_sha)
    return repo


def main(
    dataset_name_or_path,
):
    # print(token)
    if Path(dataset_name_or_path).exists():
        dataset = load_from_disk(dataset_name_or_path)
        dataset_name = os.path.basename(dataset_name_or_path)
    else:
        dataset = load_dataset(dataset_name_or_path)
        dataset_name = dataset_name_or_path.replace("/", "__")

    file_set =set()

    for code_change in tqdm(dataset["train"]):
        full_repo_name = code_change["repo"]
        user, repo_name = full_repo_name.split("/")
        commit_sha = code_change["base_commit"]
        # continue if the clone_repo fails
        try:
            repo = clone_repo(user, repo_name, commit_sha)
        except:
            continue
        file_contents = get_code_files(user, repo_name)
        for file in file_contents:
            if file in file_set:
                continue
            file_set.add(file)

    file_list = list(file_set)
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(name="my_collection")
    collection.add(
        documents=file_list,
        metadatas=[{"source" : file.split("\n")[1]} for file in file_list],
        ids = [f"id{i+1}" for i in range(len(file_list))]
    )

    # Get all embeddings
    result = collection.get(include=['embeddings'])
    # ToDo: look how GetResult object looks (turn it into a dict)
    
    # export retrieval_dict to json
    with open(f"{dataset_name}_retrieval.json", "w") as f:
        json.dump(retrieval_dict, f)
    print(f"{instance_id}: {retrieved_files}")