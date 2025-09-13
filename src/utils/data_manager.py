"""
Data management utilities
"""
import json
import os
from typing import Dict, Any
from ..config.settings import USER_DATA_FILE


def load_user_data() -> Dict[str, Any]:
    """Load user data from JSON file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_user_data(data: Dict[str, Any]):
    """Save user data to JSON file"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
