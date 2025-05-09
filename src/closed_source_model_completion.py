import json
#import openai
import argparse
import os
from tqdm import tqdm
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from openai import RateLimitError
import time

# Setting API parameters
#openai.api_key = 'API'
# Load the key from .env
from dotenv import load_dotenv
load_dotenv()
#openai.api_key = os.getenv("key")

with open("../prompts/prompt.txt", "r") as f:
    text = f.read()

client = OpenAI(api_key=os.getenv("key"), timeout=100)
# Function to fetch completion
# def fetch_completion(data_entry, model):
#     global text
#     test_case = data_entry["small_test_cases"]
#     try:
#         completions = openai.ChatCompletion.create(
#             model=model,
#             stream=False,
#             messages=[
#                 {"role": "system", "content": "You are a code developer."},
#                 {
#                     "role": "user",
#                     "content": (
#                         f"{text}\n"
#                         f"# Task description:\n```python\n{data_entry['markdown_description']}\n```\n"
#                         f"# Test case:\n```python\n{test_case}\n```"
#                     )
#                 },
#             ],
#             request_timeout=100,
#         )
#         data_entry["completion"] = completions.choices[0]["message"]["content"]
#     except Exception as e:
#         print(f"Error processing entry '{data_entry.get('id', 'unknown')}': {e}")
#         data_entry["completion"] = ""

#     return data_entry

def fetch_completion(data_entry, model):
    global text
    test_case = data_entry["small_test_cases"]
    try:
        # now .create() will time out after 100 s
        response = client.chat.completions.create(
            model=model,
            stream=False,
            messages=[
                {"role": "system", "content": "You are a code developer."},
                {
                    "role": "user",
                    "content": (
                        f"{text}\n"
                        f"# Task description:\n```python\n{data_entry['markdown_description']}\n```\n"
                        f"# Test case:\n```python\n{test_case}\n```"
                    )
                },
            ],
        )
        data_entry["completion"] = response.choices[0].message.content
    except Exception as e:
        print(f"Error processing entry '{data_entry.get('id', 'unknown')}': {e}")
        data_entry["completion"] = ""

    return data_entry


def guidelines_completion(data_entry, model, guidelines_path="../prompts/guidelines.txt"):
    # Read the guidelines from the file
    with open(guidelines_path, "r") as f:
        guidelines = f.read()
    global text
    test_case = data_entry["small_test_cases"]
    try:
        # now .create() will time out after 100 s
        response = client.chat.completions.create(
            model=model,
            stream=False,
            messages=[
            {"role": "system", "content": f"You are a code developer. Here are some guidelines for solving leetcode problems efficiently:\n{guidelines}"},
                {
                    "role": "user",
                    "content": (
                        f"{text}\n"
                        f"# Task description:\n```python\n{data_entry['markdown_description']}\n```\n"
                        f"# Test case:\n```python\n{test_case}\n```"
                    )
                },
            ],
        )
        data_entry["completion"] = response.choices[0].message.content
    except RateLimitError:
        print(f"Rate limit exceeded for entry '{data_entry.get('id', 'unknown')}'. Retrying...")
        time.sleep(60) # Wait for a minute before retrying
        return guidelines_completion(data_entry, model, guidelines_path)
    except Exception as e:
        print(f"Error processing entry '{data_entry.get('id', 'unknown')}': {e}")
        data_entry["completion"] = ""

    return data_entry

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch completions using OpenAI ChatCompletion API.')
    parser.add_argument('--model', '-m', type=str, default='gpt-4o-mini', help='Model to use for completion')
    args = parser.parse_args()
    model = args.model
    fn = "../data/dataset_with_difficulty_and_algorithm.json"

    with open(fn, "r") as f:
        dataset = json.load(f)

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_entry = {
            executor.submit(guidelines_completion, copy.deepcopy(entry), model): entry
            # executor.submit(fetch_completion, copy.deepcopy(entry), model): entry
            for entry in tqdm(dataset, desc="Submitting tasks")
        }
        for future in tqdm(as_completed(future_to_entry), total=len(future_to_entry), desc="Processing tasks"):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                error_msg = str(e)
                # Truncate overly long error messages
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + "..."
                print(f"Error updating entry '{entry.get('id', 'unknown')}': {error_msg}")

    # Ensure the results directory exists
    os.makedirs("../results", exist_ok=True)
    #output_file = f"../results/{model.replace('/', '_')}.json"
    output_file = f"../results/{model.replace('/', '_')}-guide.json"

    with open(output_file, "w") as f:
        json.dump(dataset, f, indent=4)
    print(f"Results saved to {output_file}")
