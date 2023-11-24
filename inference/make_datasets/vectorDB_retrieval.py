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

def get_embedder():
    embeddings_model = OpenAIEmbeddings()

    fs = LocalFileStore("./cache/")

    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        embeddings_model, fs, namespace=embeddings_model.model
    )
    return cached_embedder


EMBEDDING_MODEL = get_embedder()


def get_cosine_similarity(query, document):
    query_embedding = EMBEDDING_MODEL.embed_query(query)
    document_embedding = EMBEDDING_MODEL.embed_documents([document])[0]
    # turn query_embedding and document_embedding into numpy arrays
    query_embedding = np.array(query_embedding)
    document_embedding = np.array(document_embedding)
    return query_embedding.dot(document_embedding) / (
        np.linalg.norm(query_embedding) * np.linalg.norm(document_embedding)
    )

# Todo Make this function more general
def select_top_2_files(file_score_list):
    final_list = file_score_list[:2]
    return final_list

# retrieves files for a given query (problem_statement)
def file_retriever(query, files, comparison_function, selection_function):
    file_score_list = []
    for file in files:
        score = comparison_function(query, file)
        file_score_list.append((file, score))
    # sort file_score_list by score
    file_score_list.sort(key=lambda x: x[1])
    final_list = selection_function(file_score_list)
    # final_list = [file for file, score in file_score_list if score < score_threshold]
    name_list = [file.split("\n")[1] for file, score in final_list]
    # if len(final_list) == 0:
    #     final_list += [file_score_list[0]]
    return name_list


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


def get_repo_files(repo_name, commit_sha):
    token = os.environ.get("GITHUB_TOKEN", "git")
    g = Github(token)
    repo = g.get_repo(repo_name)
    commit = repo.get_commit(commit_sha)
    files = commit.files
    return files


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
            file_content = f"FileName:\n{file_path}\nCode:\n{code_content}"
            # very rough length check
            if len(file_content) > 15000:
                continue
            file_contents.append(file_content)
            # ToDo: Add file_path to the start of file contents and split file contents up into chunks
    return file_contents


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

    print(dataset)

    retrieval_dict = {}

    # use loading tqdm in this loop
    # i = 0
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
        retrieved_files = file_retriever(code_change["problem_statement"], file_contents, get_cosine_similarity, select_top_2_files)
        instance_id = code_change["instance_id"]
        retrieval_dict[instance_id] = retrieved_files
        print(f"{instance_id}: {retrieved_files}")
        # i += 1
        # if i >= 2:
        #     break
    # export retrieval_dict to json
    with open(f"{dataset_name}_retrieval.json", "w") as f:
        json.dump(retrieval_dict, f, indent=4)

       
"""
# repo = clone_repo("feedback-to-code", "cwa-server", commit_sha)
# commit = repo.get_commit(commit_sha)
# files = commit.files
# files = repo.iter_items()
# print("File: \n")
# print(files[0])
# create a list of files in the repo
# files = [file for file in repo.head.commit.tree.traverse() if file.type == "blob"]
token = os.environ.get("GITHUB_TOKEN", "git")
g = Github(token)
repo = g.get_repo(full_repo_name)
# repo.
# repo.git.checkout(commit_sha)
commit = repo.get_commit(commit_sha)
files = commit.files
print("File: \n")
print(files[0])
# file_contents = [base64.b64decode(repo.get_contents(path=file.filename, ref=commit_sha).content).decode("utf-8") for file in files]
# try the abavoe line with loops
file_contents = []
for file in files:
    print(file.filename)
    content_file = repo.get_contents(path=file.filename, ref=commit_sha)
    content = base64.b64decode(content_file.content).decode("utf-8")
    file_contents.append(content)

problem_statement = code_change["problem_statement"]
print("File Contents: \n")
print(file_contents[0])
# retrieved_files = file_retriever(problem_statement, file_contents, get_cosine_similarity)
"""


"""
collection.add(
documents=file_contents,
metadatas=[{source: repo_name} for source in file_contents],
ids = [f"id{i+1}" for i in range(len(file_contents))]
)

print(file_contents[:2])
"""
# for f in files[:2]:
#     content_file = repo.get_contents(path=f.filename, ref=commit_sha)
#     content = base64.b64decode(content_file.content).decode("utf-8")
#     print(content)

main("feedback-to-code/cwa-server-task-instances")

"""
chroma_client = chromadb.Client()

collection = chroma_client.create_collection(name="my_collection")

collection.add(
documents=[get_code_from_file("inference/make_datasets/vectorDB_retrieval.py"), get_code_from_file("inference/make_datasets/vectorDB_retrieval.py"), get_code_from_file("inference/make_datasets/utils.py")],
metadatas=[{"source": "jim"}, {"source": "jim"}, {"source": "jim"}],
ids = ["id1", "id2", "id3"]
)

results = collection.query(
query_texts="How do I use chromadb?",
n_results=2
)

print(results)"""
# repo = g.get_repo(repo_name)
# commit = repo.get_commit(commit_sha)
# files = commit.files
# chroma_client = chromadb.Client()

# collection = chroma_client.create_collection(name="my_collection")