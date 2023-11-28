import chromadb
import os
from datasets import load_from_disk, load_dataset
from pathlib import Path
import json
from tqdm import tqdm
from langchain.embeddings.openai import OpenAIEmbeddings
from chromadb.utils import embedding_functions

from utils import clone_repo, get_code_files, save_dict_to_json, get_dataset_from_huggingface

from langchain.storage import (
    LocalFileStore,
)
from langchain.embeddings import CacheBackedEmbeddings, OpenAIEmbeddings


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def get_embedder():
    embeddings_model = OpenAIEmbeddings()
    # embeddings_model = embedding_functions.DefaultEmbeddingFunction()
    fs = LocalFileStore("./cache/")
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        embeddings_model, fs, namespace=embeddings_model.model
    )
    return cached_embedder

EMBEDDING_MODEL = get_embedder()

def main(
    dataset, dataset_name
):
    print("Creating embedding json ...")
    file_set =set()
    query_set = set()
    print("Collecting Files ...")
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
        qeury = code_change["problem_statement"]
        query_set.add(qeury)

    file_list = list(file_set)
    query_list = list(query_set)
    # chroma_client = chromadb.Client()
    # When doing this we encounter a problem with chromadb
    # It seems like a bug in the library
    """
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-ada-002"
    )
    collection = chroma_client.create_collection(name="my_collection", embedding_function=openai_ef)
    print("Create Embeddings ...")
    collection.add(
        documents=file_list,
        metadatas=[{"source" : file.split("\n")[1]} for file in file_list],
        ids = [f"{i}" for i in range(len(file_list))]
    )

    embedding_dict = dict()
    # Get all embeddings
    print("Save embeddings to json ...")
    result = collection.get(include=['embeddings'])
    for id in result["ids"]:
        id = int(id)
        embedding_dict[file_list[id]] = result["embeddings"][id]
    """
    embedding_dict = {}
    n = len(file_list)
    embedding_list = EMBEDDING_MODEL.embed_documents(file_list)
    for i in tqdm(range(n)):
        file = file_list[i]
        embedding = embedding_list[i]
        embedding_dict[file] = embedding
    for i in tqdm(range(len(query_list))):
        query = query_list[i]
        embedding = EMBEDDING_MODEL.embed_query(query)
        embedding_dict[query] = embedding
    save_dict_to_json(embedding_dict, f"{dataset_name}-embeddings")


def get_embedding_dict(dataset_name_or_path):
    current_directory = os.getcwd()
    dataset, dataset_name = get_dataset_from_huggingface(dataset_name_or_path)
    if not Path(f"{current_directory}/{dataset_name}-embeddings.json").exists():
        main(dataset, dataset_name)
    with open(f"{dataset_name}-embeddings.json", "r") as f:
        embedding_dict = json.load(f)
    return embedding_dict
        