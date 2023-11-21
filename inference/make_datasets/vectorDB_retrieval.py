import chromadb
import os
from datasets import load_from_disk, load_dataset
from pathlib import Path

import logging

from github import Github
import base64


def main(
    dataset_name_or_path,
):
    g = Github("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")
    token = os.environ.get("GITHUB_TOKEN", "git")
    if Path(dataset_name_or_path).exists():
        dataset = load_from_disk(dataset_name_or_path)
        dataset_name = os.path.basename(dataset_name_or_path)
    else:
        dataset = load_dataset(dataset_name_or_path)
        dataset_name = dataset_name_or_path.replace("/", "__")

    print(dataset)
    code_change = next(iter(dataset["train"]))
    repo_name = code_change["repo"]
    commit_sha = code_change["base_commit"]
    repo = g.get_repo(repo_name)
    commit = repo.get_commit(commit_sha)
    files = commit.files

    file_contents = [base64.b64decode(repo.get_contents(path=file.filename, ref=commit_sha).content).decode("utf-8") for file in files[:5]]
    print(file_contents[:2])
    # for f in files[:2]:
    #     content_file = repo.get_contents(path=f.filename, ref=commit_sha)
    #     content = base64.b64decode(content_file.content).decode("utf-8")
    #     print(content)



main("feedback-to-code/cwa-server-task-instances")

"""
chroma_client = chromadb.Client()

collection = chroma_client.create_collection(name="my_collection")

collection.add(
    documents=["My name is Jim", "I like Volleyball"],
    metadatas=[{"source": "jim"}, {"source": "jim"}],
    ids = ["id1", "id2"]
)

results = collection.query(
    query_texts="What's my name?",
    n_results=2
)

print(results)
"""