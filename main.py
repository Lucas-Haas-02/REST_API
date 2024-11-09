from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from rsa import newkeys, encrypt, decrypt, PublicKey, PrivateKey
import base64
import hashlib
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.responses import FileResponse
import json
import os

def data_loader():
    from loader import load_bank_data
    data = load_bank_data()
    print("Loaded Data: ", data)  # Debugging print statement to verify loaded data
    return data

# Set up RSA keys
public_key, private_key = newkeys(512)

# Helper functions for RSA encryption and decryption
def encrypt_data(data: str, key: PublicKey) -> str:
    return base64.b64encode(encrypt(data.encode(), key)).decode()

def decrypt_data(data: str, key: PrivateKey) -> str:
    return decrypt(base64.b64decode(data), key).decode()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def save_bank_data(data):
    with open("bank_data.json", "w") as f:
        json.dump(data, f, indent=4)

# Models for request and response
class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class AccountUpdate(BaseModel):
    account_id: str
    balance: float

class SettingsUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None

# Authentication and login endpoint
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    data = data_loader()
    print(f"Username from form data: {form_data.username}")  # Debugging print statement for username
    user = next((user for user in data["users"] if user["username"] == form_data.username), None)
    hashed_password = hashlib.sha256(form_data.password.encode()).hexdigest()
    print(f"Hashed Password from Login: {hashed_password}")
    if user:
        print(f"User found: {user}")  # Debugging print statement for user object
        print(f"Stored Password Hash: {user['password']}")
        print(f"Length of stored password hash: {len(user['password'])}")
        print(f"Length of hashed password from login: {len(hashed_password)}")
    if user and user["password"].strip() == hashed_password:
        return {"access_token": encrypt_data(user["username"], public_key), "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")

# Check-in and get user info
@app.get("/checkin")
async def checkin(token: str = Depends(oauth2_scheme)):
    try:
        username = decrypt_data(token, private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Update account balance
@app.put("/account")
async def update_account(account_update: AccountUpdate, token: str = Depends(oauth2_scheme)):
    try:
        username = decrypt_data(token, private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    account = next((acc for acc in user["accounts"] if acc["account_id"] == account_update.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account["balance"] = account_update.balance
    save_bank_data(data)
    return {"message": "Account balance updated successfully"}

# Update user settings (username, password, email)
@app.put("/settings")
async def update_settings(settings_update: SettingsUpdate, token: str = Depends(oauth2_scheme)):
    try:
        username = decrypt_data(token, private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if settings_update.username:
        user["username"] = settings_update.username
    if settings_update.password:
        user["password"] = hashlib.sha256(settings_update.password.encode()).hexdigest()
    if settings_update.email:
        user["email"] = settings_update.email
    save_bank_data(data)
    return {"message": "Settings updated successfully"}

# Delete user account
@app.delete("/user")
async def delete_user(token: str = Depends(oauth2_scheme)):
    try:
        username = decrypt_data(token, private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    data["users"] = [user for user in data["users"] if user["username"] != username]
    save_bank_data(data)
    return {"message": "User account deleted successfully"}

# Transfer money between accounts
class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float

@app.post("/transfer")
async def transfer_money(transfer_request: TransferRequest, token: str = Depends(oauth2_scheme)):
    try:
        username = decrypt_data(token, private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from_account = next((acc for acc in user["accounts"] if acc["account_id"] == transfer_request.from_account_id), None)
    to_account = next((acc for acc in user["accounts"] if acc["account_id"] == transfer_request.to_account_id), None)
    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="Account not found")
    if from_account["balance"] < transfer_request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    from_account["balance"] -= transfer_request.amount
    to_account["balance"] += transfer_request.amount
    save_bank_data(data)
    return {"message": "Transfer completed successfully"}

@app.get("/frontend")
async def get_frontend():
    return FileResponse("banking_view.html")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
