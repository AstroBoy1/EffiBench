from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import os
import json

client = OpenAI(api_key=os.getenv("key"), timeout=100)

response = client.responses.create(
    model="gpt-4o-mini",
    input="Give guidelines on how to write time and memory efficient python code for leetcode problems. Don't" \
    "give a code example because this output will be used as part of a prompt for a code generation model to"
    "solve specific problems. "
)

print(response.output_text)
# Output the guidelines into a text file
with open("../prompts/guidelines.txt", "w", encoding="utf-8") as f:
    f.write(response.output_text)

# 3. Read your JSON file
json_path = "../data/dataset_with_difficulty_and_algorithm.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 4. Iterate through the data and add the new field
for entry in data:
    # Add the new field with the response text
    new_text = entry["markdown_description"] + "\n\n" + response.output_text
    entry["markdown_description"] = new_text

# 5. Write the updated data back to a new JSON file
output_json_path = "../data/dataset_with_difficulty_and_algorithm_with_guidelines.json"
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)