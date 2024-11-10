from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import os

from config import USERS_DATASET_PATH, MAX_RECEPIES_AT_REQUEST

from llm.gemini_for_generating_meal_plan import GeminiForMealPlanGeneration
from llm.gemini_for_personalized_recepies import GeminiForPersonalizedRecipes

from food_databases.management import RecipesStorage  # Importing RecipesStorage

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

# Define recipe model
class Recipe(BaseModel):
    name: str
    review: Optional[str] = None
    rating: Optional[float] = None
    meta: Optional[str] = None
    ingredients: List[str]
    steps: List[str]
    cooks_note: Optional[str] = None
    editors_note: Optional[str] = None
    nutrition_facts: Optional[str] = None
    url: Optional[str] = None

# Initialize RecipesStorage instance
recipes_storage = RecipesStorage()
meal_plan_generator =   GeminiForMealPlanGeneration()
gemini_recipes = GeminiForPersonalizedRecipes()


def initialize_csv():
    directory = os.path.dirname(CSV_FILE)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=User.schema()["properties"].keys())
        df.to_csv(CSV_FILE, index=False)

initialize_csv()

# Helper to load users
def load_users():
    return pd.read_csv(CSV_FILE).dropna()

# Helper to save users
def save_users(df):
    df.to_csv(CSV_FILE, index=False)

# User management endpoints
@app.post("/users/")
def create_user(user: User):
    df = load_users()
    if user.name in df['name'].values:
        raise HTTPException(status_code=400, detail="User already exists.")
    df = df._append(user.dict(), ignore_index=True)
    save_users(df)
    return {"message": "User created successfully", "user": user}

@app.get("/users/")
def get_all_users():
    df = load_users()
    return df.to_dict(orient="records")

@app.get("/users/{user_name}")
def get_user(user_name: str):
    df = load_users()
    user = df[df['name'] == user_name]
    if user.empty:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict(orient="records")[0]

@app.put("/users/{user_name}")
def update_user(user_name: str, user: User):
    df = load_users()
    user_index = df.index[df['name'] == user_name].tolist()
    if not user_index:
        raise HTTPException(status_code=404, detail="User not found")
    df.loc[user_index[0], :] = user.dict()
    save_users(df)
    return {"message": "User updated successfully", "user": user}

@app.delete("/users/{user_name}")
def delete_user(user_name: str):
    df = load_users()
    user_index = df.index[df['name'] == user_name].tolist()
    if not user_index:
        raise HTTPException(status_code=404, detail="User not found")
    df = df.drop(user_index[0])
    save_users(df)
    return {"message": "User deleted successfully"}

# Recipes management endpoints
@app.post("/recipes/")
def add_recipe(recipe: Recipe):
    recipes_storage.add(recipe.dict())
    return {"message": "Recipe added successfully", "recipe": recipe}

@app.put("/recipes/{recipe_name}")
def update_recipe(recipe_name: str, recipe: Recipe):
    updated = recipes_storage.update(recipe_name, recipe.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return {"message": "Recipe updated successfully", "recipe": recipe}

@app.delete("/recipes/{recipe_name}")
def delete_recipe(recipe_name: str):
    deleted = recipes_storage.delete(recipe_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return {"message": "Recipe deleted successfully"}

@app.post("/recipes/filter/")
def filter_recipes(positive_products: List[str], negative_products: List[str]):

    filtered_recipes = recipes_storage.filter(positive_products, negative_products)
    return {'filtered_recepies': filtered_recipes.head(MAX_RECEPIES_AT_REQUEST).to_dict()}

# Endpoint to generate a meal plan for a user by name

@app.get("/users/{user_name}/meal_plan")
def generate_meal_plan(user_name: str):
    df = load_users()
    user_row = df[df['name'] == user_name]
    
    if user_row.empty:
        raise HTTPException(status_code=404, detail="User not found")

    # Extract user parameters into a dictionary
    user_params = user_row.iloc[0].to_dict()
    
    # Generate the meal plan using the GeminiForMealPlanGeneration class
    meal_plan = meal_plan_generator(user_params=user_params)
    
    if "error" in meal_plan:
        raise HTTPException(status_code=500, detail="Error generating meal plan: " + meal_plan["error"])
    
    return {"user_name": user_name, "meal_plan": meal_plan}


@app.get("/users/{username}/recipes")
def recipes_for_user(username: str):
    # Load user data
    df = load_users()
    user = df[df['name'] == username]
    
    # Check if user exists
    if user.empty:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Extract user preferences and allergies
    user_info = user.iloc[0].to_dict()  # Get user row as dictionary
    positive_products = user_info.get("food_preferences", "")
    negative_products = user_info.get("food_allergies", "")
    specific_diet = user_info.get("specific_diet", "")
    chronic_illnesses = user_info.get("chronic_illnesses", "")


    filtered_recipes = recipes_storage.filter(str(positive_products).split(), str(negative_products).split())
    filtered_recipes = pd.concat([filtered_recipes, recipes_storage.filter([], str(negative_products).split())])

    
    # Prepare user context
    user_context = {
        "preferred_products": positive_products,
        "allergic_products": negative_products,
        "specific_diet": specific_diet,
        "chronic_illnesses": chronic_illnesses,
    }
    
    personalized_recepies = list() 
    for i in range(3): 
        personalized_recepies.append(gemini_recipes(user_context, filtered_recipes.iloc[i]))    

    return {"username": username, "personalized_recipes": personalized_recepies, "other_recepies": filtered_recipes.iloc[3:MAX_RECEPIES_AT_REQUEST]}
