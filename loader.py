from main import save_bank_data
import json
import os
from fastapi import HTTPException
# Load dummy data from a separate file
def load_bank_data():
    try:
        if not os.path.exists("bank_data.json"):
            # Initialize bank_data.json if it doesn't exist
            initial_data = {
                "users": []
            }
            save_bank_data(initial_data)
        with open("bank_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data file not found.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Data file format is incorrect.")