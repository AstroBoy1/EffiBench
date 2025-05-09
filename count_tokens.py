import json

# Load the JSON file
file_path = "./data/dataset_with_difficulty_and_algorithm.json"
with open(file_path, "r") as f:
    dataset = json.load(f)

# Count characters
total_characters = 0
for entry in dataset:
    text = f"{entry['markdown_description']} {entry['small_test_cases']}"
    total_characters += len(text)

print(f"Total characters in the JSON file: {total_characters}")
# 1,485,365
# 1usd per million for mini 4o