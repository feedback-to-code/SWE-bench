import numpy as np
from tqdm import tqdm

from utils import clone_repo, get_code_files, save_dict_to_json, get_dataset_from_huggingface
from create_embedding_dict import get_embedding_dict


def get_cosine_similarity(query, document, embedding_dict):
    query_embedding = embedding_dict[query]
    document_embedding = embedding_dict[document]
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
def file_retriever(query, files, embedding_dict, comparison_function, selection_function):
    file_score_list = []
    for file in files:
        score = comparison_function(query, file, embedding_dict)
        file_score_list.append((file, score))
    # sort file_score_list by score
    file_score_list.sort(key=lambda x: x[1])
    final_list = selection_function(file_score_list)
    name_list = [file.split("\n")[1] for file, score in final_list]
    return name_list


def main(
    dataset_name_or_path,
):
    dataset, dataset_name = get_dataset_from_huggingface(dataset_name_or_path)
    embedding_dict = get_embedding_dict(dataset_name_or_path)
    # embedding_dict = {}
    retrieval_dict = {}
    # iterate over every code change in the dataset
    # checkout the repo to the base commit
    # and retrieve the files
    # Then save to json
    print("Retrieving files ...")
    for code_change in tqdm(dataset["train"]):
        full_repo_name = code_change["repo"]
        user, repo_name = full_repo_name.split("/")
        commit_sha = code_change["base_commit"]
        try:
            repo = clone_repo(user, repo_name, commit_sha)
        except:
            continue
        file_contents = get_code_files(user, repo_name)
        retrieved_files = file_retriever(code_change["problem_statement"], file_contents, embedding_dict, get_cosine_similarity, select_top_2_files)
        instance_id = code_change["instance_id"]
        retrieval_dict[instance_id] = retrieved_files
        print(f"{instance_id}: {retrieved_files}")
    print("Saving retrieval dict to json ...")
    save_dict_to_json(retrieval_dict, f"{dataset_name}-retrieval")


def retrieve_file(repository_name):
    main(repository_name)


if __name__ == "__main__":
    main("feedback-to-code/cwa-server-task-instances")