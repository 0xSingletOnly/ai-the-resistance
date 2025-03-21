import json
import argparse
import random

def process_jsonl_file(input_file, output_train_file, output_test_file, train_ratio=0.85):
    # Read the input jsonl file and collect all entries
    entries = []
    with open(input_file, 'r') as f_in:
        for line in f_in:
            try:
                entry = json.loads(line.strip())
                
                # Extract prompt and response
                if "prompt" in entry and "response" in entry:
                    # Clean the response (remove markdown code tags if present)
                    response = entry["response"]
                    if response.startswith("`json") and response.endswith("`"):
                        response = response[5:-1].strip()
                    elif response.startswith("`") and response.endswith("`"):
                        response = response[1:-1].strip()
                    
                    # Create a new entry with this prompt-response pair
                    output_entry = {
                        "messages": [
                            {
                                "role": "user",
                                "content": entry["prompt"]
                            },
                            {
                                "role": "assistant",
                                "content": response
                            }
                        ]
                    }
                    entries.append(output_entry)
            except json.JSONDecodeError:
                print(f"Error parsing line: {line}")
                continue

    # Shuffle the entries
    random.shuffle(entries)
    
    # Calculate split point
    split_idx = int(len(entries) * train_ratio)
    train_entries = entries[:split_idx]
    test_entries = entries[split_idx:]
    
    # Write training set
    with open(output_train_file, 'w') as f_train:
        for entry in train_entries:
            f_train.write(json.dumps(entry) + '\n')
    
    # Write test set
    with open(output_test_file, 'w') as f_test:
        for entry in test_entries:
            f_test.write(json.dumps(entry) + '\n')
    
    print(f"Total entries processed: {len(entries)}")
    print(f"Training set size: {len(train_entries)}")
    print(f"Test set size: {len(test_entries)}")
    print(f"Training data saved to {output_train_file}")
    print(f"Test data saved to {output_test_file}")

# Usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process JSONL file to create training and test datasets')
    parser.add_argument('input_file', help='Input JSONL file to process')
    parser.add_argument('output_train_file', help='Output JSON file for training data')
    parser.add_argument('output_test_file', help='Output JSON file for test data')
    parser.add_argument('--train-ratio', type=float, default=0.85, 
                      help='Ratio of data to use for training (default: 0.85)')
    
    args = parser.parse_args()
    process_jsonl_file(args.input_file, args.output_train_file, args.output_test_file, args.train_ratio)