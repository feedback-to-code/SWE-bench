from datasets import load_dataset
import tiktoken

dataset = load_dataset("feedback-to-code/SWE-bench__style-3__fs-oracle_large_tokenlength")

# Function to filter rows based on token length
def filter_by_token_length(example):
    tokenized = tokenizer(example['text'])  # Assuming tokenizer is a tokenizer instance used in the dataset
    return len(tokenized['input_ids']) >= 15000

tokenizer = tiktoken.
# Apply the filter function to remove rows
filtered_dataset = dataset.filter(filter_by_token_length)

# Display the number of examples after filtering
print("Number of examples after filtering:", len(filtered_dataset))
