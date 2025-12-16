import json
import os

MEMORY_FILE = "conversation_memory.json"

class Memory:
    def __init__(self):
        if not os.path.exists(MEMORY_FILE):
             with open(MEMORY_FILE, 'w') as f:
                 json.dump({}, f)
    
    def get_history(self, user_id: str) -> list:
        with open(MEMORY_FILE, 'r') as f:
            data = json.load(f)
        return data.get(user_id, [])

    def add_message(self, user_id: str, role: str, content: str):
        with open(MEMORY_FILE, 'r') as f:
            data = json.load(f)
        
        if user_id not in data:
            data[user_id] = []
        
        data[user_id].append({"role": role, "content": content})
        
        with open(MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
