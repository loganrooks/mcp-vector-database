import json
from typing import List, Optional, Dict, Any

def format_vector_for_pgvector(vector: List[float]) -> str:
    """Formats a list of floats into the string representation required by pgvector."""
    # Convert list to string format like '[1.0,2.0,3.0]'
    return '[' + ','.join(map(str, vector)) + ']'

def json_serialize(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """Serializes a dictionary to a JSON string, returning None if input is None."""
    if data is None:
        return None
    try:
        # Use separators=(',', ':') for compact representation
        return json.dumps(data, separators=(',', ':'))
    except TypeError as e:
        # Log or handle potential serialization errors
        print(f"Error serializing data to JSON: {e}") # Replace with proper logging
        return None