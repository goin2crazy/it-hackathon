from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import os

from config import USERS_DATASET_PATH

app = FastAPI()

# CSV file path
CSV_FILE = USERS_DATASET_PATH

# Define user model
class User(BaseModel):
    name: str
    date_of_birth: str
    gender: Optional[str] = None
    condition: Optional[str] = None
    food_allergies: Optional[str] = None
    specific_diet: Optional[str] = None
    chronic_illnesses: Optional[str] = None
    symptoms: Optional[str] = None
    food_preferences: Optional[str] = None
    medication: Optional[str] = None

def initialize_csv():
    # Get the directory path from CSV_FILE
    directory = os.path.dirname(CSV_FILE)
    
    # Create directory if it doesn't exist
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Initialize CSV file if it doesn't exist
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=User.schema()["properties"].keys())
        df.to_csv(CSV_FILE, index=False)

initialize_csv()

# Helper to load users
def load_users():
    return pd.read_csv(CSV_FILE)

# Helper to save users
def save_users(df):
    df.to_csv(CSV_FILE, index=False)

# Endpoint to create a new user
@app.post("/users/")
def create_user(user: User):
    df = load_users()
    if user.name in df['name'].values:
        raise HTTPException(status_code=400, detail="User already exists.")
    df = df._append(user.dict(), ignore_index=True)
    save_users(df)
    return {"message": "User created successfully", "user": user}

# Endpoint to get all users
@app.get("/users/")
def get_all_users():
    df = load_users()
    return df.to_dict(orient="records")

# Endpoint to get a specific user by name
@app.get("/users/{user_name}")
def get_user(user_name: str):
    df = load_users()
    user = df[df['name'] == user_name]
    if user.empty:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict(orient="records")[0]

# Endpoint to update a user's information
@app.put("/users/{user_name}")
def update_user(user_name: str, user: User):
    df = load_users()
    user_index = df.index[df['name'] == user_name].tolist()
    if not user_index:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user data
    df.loc[user_index[0], :] = user.dict()
    save_users(df)
    return {"message": "User updated successfully", "user": user}

# Endpoint to delete a user
@app.delete("/users/{user_name}")
def delete_user(user_name: str):
    df = load_users()
    user_index = df.index[df['name'] == user_name].tolist()
    if not user_index:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Drop the user and save
    df = df.drop(user_index[0])
    save_users(df)
    return {"message": "User deleted successfully"}
