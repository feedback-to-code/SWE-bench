import pandas as pd
from utils import find_files

pred = pd.read_json("../data/cwa_server/predictions.jsonl", lines=True)
df = pd.read_json("../data/cwa_server/cwa-server-task-instances.jsonl", lines=True)
pred = pred.set_index("instance_id")
df = df.set_index("instance_id")
all = pred.join(df)
all = all.rename(columns={"text": "prompt", "model_patch": "prediction"})
all["id"] = all["pull_number"]
all.index = all["id"]
all["pr_link"] = all.apply(
    lambda x: f"https://github.com/{x.repo}/pull/{x.pull_number}", axis=1
)
# here each pr has only 1 issue
all["issue_link"] = all.apply(
    lambda x: f"https://github.com/{x.repo}/issues/{x.issue_numbers[0]}", axis=1
)
all["oracle_files"] = all.prompt.apply(find_files)
all = all.drop(
    columns=[
        "model_name_or_path",
        "full_output",
        "created_at",
        "test_patch",
        "repo",
        "pull_number",
        "issue_numbers",
        "prompt",
        "hints_text",
    ]
)
all = all[
    [
        "problem_statement",
        "issue_link",
        "pr_link",
        "patch",
        "prediction",
        "oracle_files",
        "base_commit",
    ]
]

command = all.apply(lambda x: f"python3 create_patchfiles.py {x.name}", axis=1)

all.insert(0, "command", command)

all.to_csv("../data/cwa_server/evaluation.csv", index=True)

print("Done")
