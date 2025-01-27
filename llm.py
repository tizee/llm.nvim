import argparse
import os
import sys
import yaml
import json
from openai import OpenAI
import sqlite3
from datetime import datetime

import io
# UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# ensure no buffering for streaming output
sys.stdout.reconfigure(line_buffering=True)

# Load configuration from a YAML file
def load_model_config(config_path):
    if not os.path.exists(config_path):
        return []
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or []

# Load API keys from a JSON file
def load_api_keys(api_keys_path):
    if not os.path.exists(api_keys_path):
        return {}
    with open(api_keys_path, 'r') as f:
        return json.load(f)

# Initialize the SQLite database
def init_db(db_path):
    # Ensure the directory for the db_path exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create a new connection (this will create the file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            model_name TEXT,
            prompt TEXT,
            answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Log the conversation to the database
def log_conversation(conversation_id, model_name, prompt, answer, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (conversation_id, model_name, prompt, answer)
        VALUES (?, ?, ?, ?)
    ''', (conversation_id, model_name, prompt, answer))
    conn.commit()
    conn.close()

# Function to interact with the LLM model
def interact_with_model(model_name, prompt, system_prompt=None, api_key=None, api_base=None, can_stream=True, conversation_id=None, db_path=None):
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=can_stream
    )

    # Stream the response
    answer = ""
    for chunk in response:
        delta = chunk.choices[0].delta
        if hasattr(delta, 'reasoning_content'):
            reasoning_content = delta.reasoning_content
            if reasoning_content:
                print(reasoning_content, end='', flush=True)
                answer += reasoning_content
        else:
            content = delta.content
            print(content, end='', flush=True)
            answer += content

    # Indicate the end of the response
    print("\n")

    # Log the conversation
    if conversation_id and db_path:
        log_conversation(conversation_id, model_name, prompt, answer, db_path)

    return answer

def find_model_config(model_id, model_configs):
    for config in model_configs:
        if config['model_id'] == model_id:
            return config
    return None

def print_logs(db_path):
    # Ensure the database file exists before trying to read from it
    if not os.path.exists(db_path):
        print("Error: Logs database does not exist.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM conversations ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        _, conversation_id, model_name, prompt, answer, timestamp = row
        print(f"# {timestamp} conversation: \t{conversation_id}\n")
        print(f" Model: **{model_name}**\n")
        print("## Prompt:\n")
        print(prompt)
        print("\n## Response:\n")
        print(answer)
        print("\n---\n")

def main():
    parser = argparse.ArgumentParser(description='CLI tool to interact with LLM models.')
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for the logs command
    parser_logs = subparsers.add_parser('logs', help='Print logs in Markdown format')
    parser_logs.add_argument('--db-path', default='~/.config/llm/llm_logs.db', help='Path to the SQLite database')

    # Subparser for interacting with the model
    parser_model = subparsers.add_parser('model', help='Interact with an LLM model')
    parser_model.add_argument('-m', '--model-id', required=True, help='Model ID')
    parser_model.add_argument('--config', default='~/.config/llm/llm.vim.yaml', help='Path to the model configuration file')
    parser_model.add_argument('--api-keys', default='~/.config/llm/keys.json', help='Path to the API keys file')
    parser_model.add_argument('--system-prompt', default=None, help='System prompt to be used')
    parser_model.add_argument('--conversation-id', default=None, help='Conversation ID')
    parser_model.add_argument('--db-path', default='~/.config/llm/llm_logs.db', help='Path to the SQLite database')

    args, unknown = parser.parse_known_args()

    db_path = os.path.expanduser(args.db_path)
    init_db(db_path)

    if args.command == 'logs':
        print_logs(db_path)
        return

    if args.command != 'model':
        parser.print_help()
        sys.exit(1)

    # Load model configurations
    config_path = os.path.expanduser(args.config)
    model_configs = load_model_config(config_path)

    # Load API keys
    api_keys_path = os.path.expanduser(args.api_keys)
    api_keys = load_api_keys(api_keys_path)

    # Find the matching model configuration
    model_config = find_model_config(args.model_id, model_configs)
    if not model_config:
        print("Error: Model ID not found in configuration.")
        sys.exit(1)

    # Extract necessary parameters from the model configuration
    model_name = model_config['model_name']
    api_base = model_config['api_base']
    can_stream = model_config['can_stream']
    api_key_name = model_config['api_key_name']
    api_key = api_keys.get(api_key_name)

    if not api_key:
        print("Error: API key not found for the specified model.")
        sys.exit(1)

    # Determine the prompt
    if len(unknown) > 0:
        prompt = ' '.join(unknown)
    else:
        prompt = sys.stdin.read().strip()

    if not prompt:
        print("Error: No prompt provided.")
        sys.exit(1)

    # Generate a unique conversation ID if not provided
    if not args.conversation_id:
        args.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

    # Interact with the model
    interact_with_model(model_name, prompt, args.system_prompt, api_key, api_base, can_stream, args.conversation_id, db_path)

if __name__ == '__main__':
    main()
