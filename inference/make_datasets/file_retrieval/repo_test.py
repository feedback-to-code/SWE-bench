"""
from git import Repo

# Open an existing repo
repo = Repo('/path/to/repo')

# Access branches
branches = repo.branches
print(branches)

# Access commits
commits = repo.commits()

print(commits)

# Create a new commit
# index = repo.index
# index.add(['file.txt'])
# index.commit("My commit message")

# Checkout a branch
repo.git.checkout(branches[0])
"""
"""
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

embeddings_model = OpenAIEmbeddings()

fs = LocalFileStore("./cache/")

cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    embeddings_model, fs, namespace=embeddings_model.model
)

embeddings = cached_embedder.embed_documents(
    [
        "Hi there!",
        "Oh, hello!",
        "What's your name?",
        "My friends call me World",
        "Hello World!"
    ]
)

embedded_query = cached_embedder.embed_query("What was the name mentioned in the conversation?")
print(embedded_query[:5])
"""
"""
fs = LocalFileStore("./cache/")

cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    embeddings_model, fs, namespace=embeddings_model.model
)

raw_documents = TextLoader("inference/make_datasets/repo_test.py").load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
documents = text_splitter.split_documents(raw_documents)

db = FAISS.from_documents(documents, cached_embedder)

db2 = FAISS.from_documents(documents, cached_embedder)

print(list(fs.yield_keys())[:5])
"""
import os
for root, dirs, files in os.walk("feedback-to-code__cwa-server"):
    for file in files:
        print(f"File: {os.path.join(root, file)}")
    for file in dirs:
        print(f"Dir: {os.path.join(root, file)}")