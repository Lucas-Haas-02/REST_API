from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from rsa import newkeys, encrypt, decrypt, PublicKey, PrivateKey
import json
import base64
import hashlib
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

# Dummy data to simulate banking system
with open("bank_data.json", "w") as f:
    json.dump({
        "users": [{
            "username": "user1",
            "password": hashlib.sha256("password1".encode()).hexdigest(),
            "email": "user1@bank.com",
            "accounts": [{
                "account_id": "001",
                "balance": 5000
            }, {
                "account_id": "002",
                "balance": 3000
            }]
        }]
    }, f)

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
    with open("bank_data.json", "r") as f:
        data = json.load(f)
    user = next((user for user in data["users"] if user["username"] == form_data.username), None)
    if user and user["password"] == hashlib.sha256(form_data.password.encode()).hexdigest():
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
    with open("bank_data.json", "r") as f:
        data = json.load(f)
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
    with open("bank_data.json", "r") as f:
        data = json.load(f)
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    account = next((acc for acc in user["accounts"] if acc["account_id"] == account_update.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account["balance"] = account_update.balance
    with open("bank_data.json", "w") as f:
        json.dump(data, f)
    return {"message": "Account balance updated successfully"}

# Update user settings (username, password, email)
@app.put("/settings")
async def update_settings(settings_update: SettingsUpdate, token: str = Depends(oauth2_scheme)):
    try:
        username = decrypt_data(token, private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    with open("bank_data.json", "r") as f:
        data = json.load(f)
    user = next((user for user in data["users"] if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if settings_update.username:
        user["username"] = settings_update.username
    if settings_update.password:
        user["password"] = hashlib.sha256(settings_update.password.encode()).hexdigest()
    if settings_update.email:
        user["email"] = settings_update.email
    with open("bank_data.json", "w") as f:
        json.dump(data, f)
    return {"message": "Settings updated successfully"}

# Delete user account
@app.delete("/user")
async def delete_user(token: str = Depends(oauth2_scheme)):
    try:
        username = decrypt_data(token, private_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    with open("bank_data.json", "r") as f:
        data = json.load(f)
    data["users"] = [user for user in data["users"] if user["username"] != username]
    with open("bank_data.json", "w") as f:
        json.dump(data, f)
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
    with open("bank_data.json", "r") as f:
        data = json.load(f)
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
    with open("bank_data.json", "w") as f:
        json.dump(data, f)
    return {"message": "Transfer completed successfully"}

# Frontend - HTML and JavaScript
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Banking System</title>
    <script>
        let token = "";

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const response = await fetch('http://127.0.0.1:8000/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `username=${username}&password=${password}`,
            });
            const data = await response.json();
            if (response.ok) {
                token = data.access_token;
                document.getElementById('login').style.display = 'none';
                document.getElementById('menu').style.display = 'block';
            } else {
                alert('Login failed: ' + data.detail);
            }
        }

        function showSettings() {
            document.getElementById('menu').style.display = 'none';
            document.getElementById('settings').style.display = 'block';
        }

        function showBanking() {
            document.getElementById('menu').style.display = 'none';
            document.getElementById('banking').style.display = 'block';
        }

        async function updateSettings() {
            const newUsername = document.getElementById('newUsername').value;
            const newPassword = document.getElementById('newPassword').value;
            const newEmail = document.getElementById('newEmail').value;
            const response = await fetch('http://127.0.0.1:8000/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ username: newUsername, password: newPassword, email: newEmail }),
            });
            const data = await response.json();
            if (response.ok) {
                alert(data.message);
                document.getElementById('settings').style.display = 'none';
                document.getElementById('menu').style.display = 'block';
            } else {
                alert('Failed to update settings: ' + data.detail);
            }
        }

        async function checkin() {
            const response = await fetch('http://127.0.0.1:8000/checkin', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });
            const data = await response.json();
            if (response.ok) {
                document.getElementById('bankingInfo').innerText = JSON.stringify(data.accounts, null, 2);
            } else {
                alert('Check-in failed: ' + data.detail);
            }
        }

        async function updateAccountBalance() {
            const accountId = document.getElementById('accountId').value;
            const newBalance = document.getElementById('newBalance').value;
            const response = await fetch('http://127.0.0.1:8000/account', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ account_id: accountId, balance: parseFloat(newBalance) }),
            });
            const data = await response.json();
            if (response.ok) {
                alert(data.message);
                checkin();
            } else {
                alert('Failed to update account balance: ' + data.detail);
            }
        }
    </script>
</head>
<body>
    <h1>Banking System</h1>
    <div id="login">
        <h2>Login</h2>
        <input type="text" id="username" placeholder="Username">
        <input type="password" id="password" placeholder="Password">
        <button onclick="login()">Login</button>
    </div>
    <div id="menu" style="display:none;">
        <h2>Menu</h2>
        <button onclick="showSettings()">Update Settings</button>
        <button onclick="showBanking()">Banking Information</button>
    </div>
    <div id="settings" style="display:none;">
        <h2>Update Settings</h2>
        <input type="text" id="newUsername" placeholder="New Username">
        <input type="password" id="newPassword" placeholder="New Password">
        <input type="email" id="newEmail" placeholder="New Email">
        <button onclick="updateSettings()">Save Changes</button>
        <button onclick="document.getElementById('settings').style.display='none'; document.getElementById('menu').style.display='block';">Cancel</button>
    </div>
    <div id="banking" style="display:none;">
        <h2>Banking Information</h2>
        <button onclick="checkin()">View Account Info</button>
        <pre id="bankingInfo"></pre>
        <input type="text" id="accountId" placeholder="Account ID">
        <input type="number" id="newBalance" placeholder="New Balance">
        <button onclick="updateAccountBalance()">Update Account Balance</button>
        <button onclick="document.getElementById('banking').style.display='none'; document.getElementById('menu').style.display='block';">Back to Menu</button>
    </div>
</body>
</html>
"""

@app.get("/frontend")
async def get_frontend():
    return Response(content=html_content, media_type="text/html")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
