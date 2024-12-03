from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from rsa import newkeys, encrypt, decrypt, PublicKey, PrivateKey
import base64
import hashlib
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
import json
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
import re
import random

# Secret key for JWT token generation
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Load bank data from JSON file
def data_loader():
    with open("bank_data.json", "r") as f:
        data = json.load(f)
    return data

# Save bank data to JSON file
def save_bank_data(data):
    with open("bank_data.json", "w") as f:
        json.dump(data, f, indent=4)

# Set up RSA keys
public_key, private_key = newkeys(512)

# Helper functions for RSA encryption and decryption
def encrypt_data(data: str, key: PublicKey) -> str:
    return base64.b64encode(encrypt(data.encode(), key)).decode()

def decrypt_data(data: str, key: PrivateKey) -> str:
    return decrypt(base64.b64decode(data), key).decode()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_unique_account_number(data):
    while True:
        account_number = str(random.randint(100000000, 999999999))
        if not any(account_number == acc["account_id"] for user in data["users"] for acc in user["accounts"]):
            return account_number

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

# Models for request and response
class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class AccountUpdate(BaseModel):
    account_id: str
    amount: str  # Changed to string to handle + or - prefixes

class SettingsUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None

class CreateAccountRequest(BaseModel):
    username: str

# Authentication and login endpoint
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    data = data_loader()
    user = next((user for user in data["users"] if user["username"].lower() == form_data.username.lower()), None)
    hashed_password = hashlib.sha256(form_data.password.encode()).hexdigest()
    if user and user["password"].strip() == hashed_password:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")

# Check-in and get user info
@app.get("/checkin")
async def checkin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user, "accounts": user["accounts"]}

# Create a new account number
@app.post("/create_account_number")
async def create_account_number(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_account_number = generate_unique_account_number(data)
    user["accounts"].append({"account_id": new_account_number, "balance": 0.0})
    save_bank_data(data)
    return JSONResponse(status_code=201, content={"account_id": new_account_number, "clear_fields": True})

# Update account balance (deposit/withdraw)
@app.put("/account/update_balance")
async def update_account_balance(account_update: AccountUpdate, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    account = next((acc for acc in user["accounts"] if acc["account_id"] == account_update.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    try:
        # Determine whether to deposit or withdraw based on the prefix
        if account_update.amount.startswith('+'):
            account["balance"] += float(account_update.amount[1:])
        elif account_update.amount.startswith('-'):
            withdrawal_amount = float(account_update.amount[1:])
            if withdrawal_amount > account["balance"]:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            account["balance"] -= withdrawal_amount
        else:
            raise HTTPException(status_code=400, detail="Invalid amount format. Use + or - to indicate transaction type.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid amount. Must be a number prefixed with + or -.")

    save_bank_data(data)
    return JSONResponse(status_code=200, content={"message": "Account balance updated successfully", "clear_fields": True})

# Update user settings (username, password, email)
@app.put("/settings/update")
async def update_settings(settings_update: SettingsUpdate, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    data = data_loader()
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found", "clear_fields": True})

    # Validate email if updated
    if settings_update.email:
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(email_pattern, settings_update.email):
            return JSONResponse(status_code=400, content={"message": "Invalid email format", "clear_fields": True})

    # Validate password if updated
    if settings_update.password:
        if len(settings_update.password) < 8 or not re.search(r'[A-Z]', settings_update.password) or not re.search(r'[0-9]', settings_update.password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', settings_update.password):
            return JSONResponse(status_code=400, content={"message": "Password must be at least 8 characters long and include at least one uppercase letter, one number, and one special character", "clear_fields": True})

    # Update user settings
    if settings_update.username and settings_update.username.lower() != user["username"].lower():
        # Ensure the new username is not already taken
        if any(existing_user["username"].lower() == settings_update.username.lower() for existing_user in data["users"]):
            return JSONResponse(status_code=400, content={"message": "Username already exists", "clear_fields": True})
        user["username"] = settings_update.username
    if settings_update.password:
        user["password"] = hashlib.sha256(settings_update.password.encode()).hexdigest()
    if settings_update.email and settings_update.email.lower() != user["email"].lower():
        # Ensure the new email is not already taken
        if any(existing_user["email"].lower() == settings_update.email.lower() for existing_user in data["users"]):
            return JSONResponse(status_code=400, content={"message": "Email already exists", "clear_fields": True})
        user["email"] = settings_update.email
    
    save_bank_data(data)
    return JSONResponse(status_code=200, content={"message": "Settings updated successfully", "clear_fields": True})

# Logout endpoint to invalidate session and return to home page with fields cleared
@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    return RedirectResponse(url="/frontend")

@app.get("/frontend")
async def get_frontend():
    return FileResponse("banking_view.html")

# Endpoint to create a new account
@app.post("/create_account")
async def create_account(user: User):
    if not user.username or not user.email or not user.password:
        return JSONResponse(status_code=400, content={"message": "Please fill in all fields", "clear_fields": True})

    # Validate email
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if not re.match(email_pattern, user.email):
        return JSONResponse(status_code=400, content={"message": "Invalid email format", "clear_fields": True})

    # Validate password
    if len(user.password) < 8 or not re.search(r'[A-Z]', user.password) or not re.search(r'[0-9]', user.password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', user.password):
        return JSONResponse(status_code=400, content={"message": "Password must be at least 8 characters long and include at least one uppercase letter, one number, and one special character", "clear_fields": True})

    data = data_loader()

    # Check if username or email already exists
    for existing_user in data["users"]:
        if existing_user["username"].lower() == user.username.lower():
            return JSONResponse(status_code=400, content={"message": "Username already exists", "clear_fields": True})
        if existing_user["email"].lower() == user.email.lower():
            return JSONResponse(status_code=400, content={"message": "Email already exists", "clear_fields": True})

    # Hash the password for security
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()

    # Create new user data
    new_user = {
        "username": user.username,
        "password": hashed_password,
        "email": user.email,
        "accounts": []
    }

    # Add the new user to users data
    data["users"].append(new_user)
    save_bank_data(data)

    return JSONResponse(status_code=201, content={"message": "Account created successfully", "clear_fields": True})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
