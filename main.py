# Step 1: Install FastAPI
# Make sure FastAPI and Uvicorn are installed. You can install them using pip:
# pip install fastapi uvicorn

# Step 2: Create a Python file for your RESTful API
# Save this code in a file called main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import HTMLResponse

import random
import RSA_Encryption

app = FastAPI()

p1 = RSA_Encryption.prime_list[random.randint(0, len(RSA_Encryption.prime_list)) - 1]
p2 = RSA_Encryption.prime_list[random.randint(0, len(RSA_Encryption.prime_list)) - 1]
print("The p = " + str(p1) + " and q = " + str(p2))
test_keys = RSA_Encryption.key_gen(p1, p2)

RSA_Encryption.prep_function(RSA_Encryption.rsa(RSA_Encryption.prep_function(""), test_keys[0]))

# Sample data to simulate a database
items = [
    {"id": 1, "name": RSA_Encryption.prep_function(RSA_Encryption.rsa(RSA_Encryption.prep_function("Item 1"), test_keys[0])), "description": RSA_Encryption.prep_function(RSA_Encryption.rsa(RSA_Encryption.prep_function("This is item 1"), test_keys[0]))},
    {"id": 2, "name": RSA_Encryption.prep_function(RSA_Encryption.rsa(RSA_Encryption.prep_function("Item 2"), test_keys[0])), "description": RSA_Encryption.prep_function(RSA_Encryption.rsa(RSA_Encryption.prep_function("This is item 2"), test_keys[0]))}
]


# Pydantic model for item
class Item(BaseModel):
    name: str
    description: str


# Home route with a polished UI to confirm the API is running
@app.get('/', response_class=HTMLResponse)
def home():
    html_content = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Simple RESTful API</title>
        <style>
          body { font-family: Arial, sans-serif; background-color: #f0f0f0; margin: 0; padding: 20px; }
          .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
          h1 { color: #333; }
          ul { line-height: 1.6; }
          a { color: #007bff; text-decoration: none; }
          a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Welcome to the Simple RESTful API</h1>
          <p>Use the endpoints to interact with the API:</p>
          <ul>
            <li><a href="/items" target="_blank">GET /items</a> - Get all items</li>
            <li>GET /items/{id} - Get item by ID</li>
            <li>POST /items - Add a new item</li>
          </ul>
        </div>
      </body>
    </html>
    """
    return html_content

# RESTful route to get all items
@app.get('/items', response_model=List[dict])
def get_items():
    return items

# RESTful route to get an item by ID
@app.get('/items/{item_id}', response_model=Optional[dict])
def get_item(item_id: int):
    item = next((item for item in items if item['id'] == item_id), None)
    if item:
        return item
    else:
        raise HTTPException(status_code=404, detail="Item not found")

# RESTful route to add a new item
@app.post('/items', response_model=dict)
def add_item(new_item: Item):
    item_id = len(items) + 1
    item = {"id": item_id, "name": new_item.name, "description": new_item.description}
    items.append(item)
    return item

if __name__ == '__main__':
    # Run the FastAPI app with Uvicorn
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# Step 3: Run the API
# Open your terminal, navigate to the folder where main.py is located, and run the following command:
# uvicorn main:app --reload

# Step 4: Test the API
# You can use a tool like Postman or your browser to test the API endpoints.
# - To get all items, go to http://127.0.0.1:8000/items
# - To add a new item, send a POST request to http://127.0.0.1:8000/items with JSON data like:
#   {
#       "name": "New Item",
#       "description": "This is a new item."
#   }
