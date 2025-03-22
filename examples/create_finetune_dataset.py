import argparse
import json
import os
import random
import asyncio
from typing import List, Dict
from itertools import islice

from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=os.getenv("DEEPSEEK_API_BASE_URL"))
MODEL = "deepseek-chat"
BATCH_SIZE = 3  # Process 3 rows concurrently

async def generate_new_response(prompt: str, response: str) -> str:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        updated_response = response.choices[0].message.content
    except Exception as e:
        print(f"LLM API call failed: {e}")
        updated_response = response

    return updated_response

async def process_batch(batch: List[Dict]) -> List[Dict]:
    tasks = []
    for entry in batch:
        if "prompt" in entry and "response" in entry:
            # Clean the response
            response = entry["response"]
            if response.startswith("`json") and response.endswith("`"):
                response = response[5:-1].strip()
            elif response.startswith("`") and response.endswith("`"):
                response = response[1:-1].strip()
            
            tasks.append(generate_new_response(entry["prompt"], response))
    
    if not tasks:
        return []
    
    responses = await asyncio.gather(*tasks)
    
    result = []
    for entry, new_response in zip(batch, responses):
        # Print the original prompt and new response for inspection
        print("\n" + "="*80)
        print("\nGENERATED RESPONSE:")
        print(new_response)
        print("="*80)
        
        output_entry = {
            "messages": [
                {
                    "role": "user",
                    "content": entry["prompt"]
                },
                {
                    "role": "assistant",
                    "content": new_response
                }
            ]
        }
        result.append(output_entry)
    
    return result

def get_batch(file_iterator, size: int) -> List[Dict]:
    batch = []
    try:
        for _ in range(size):
            line = next(file_iterator)
            try:
                entry = json.loads(line.strip())
                batch.append(entry)
            except json.JSONDecodeError:
                print(f"Error parsing line: {line}")
                continue
    except StopIteration:
        pass
    return batch

def process_jsonl_file(input_file: str, output_file: str):
    entries = []
    
    with open(input_file, 'r') as f_in:
        batch_count = 0
        while True:
            batch = get_batch(f_in, BATCH_SIZE)
            if not batch:
                break
                
            batch_count += 1
            print(f"Processing batch {batch_count}")
            
            # Process the batch
            processed_entries = asyncio.run(process_batch(batch))
            entries.extend(processed_entries)

    random.shuffle(entries)
    
    # Write training set
    with open(output_file, 'w') as f_out:
        for entry in entries:
            f_out.write(json.dumps(entry) + '\n')
    
    print(f"Total entries processed: {len(entries)}")
    print(f"Train set size: {len(entries)}")
    print(f"Training data saved to {output_file}")

# Usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process JSONL file to create train dataset')
    parser.add_argument('input_file', help='Input JSONL file to process')
    parser.add_argument('output_file', help='Output JSON file for train data')
    
    args = parser.parse_args()
    process_jsonl_file(args.input_file, args.output_file)