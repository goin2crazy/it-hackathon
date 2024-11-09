import pandas as pd
import ast
from .config import (
    RES_DATA_PATH, 
    DIABETES_DATA_PATH, 
    ALLERGIC_DATA_PATH  # Fixed typo: ALLARGIC_DATA_PATH
)


class RecipesStorage:
    def __init__(self):
        # Load the dataframe from RES_DATA_PATH
        # Columns: name, review, rating, meta, ingredients, steps, cooks_note, editors_note, nutrition_facts, url
        self.df = pd.read_csv(RES_DATA_PATH)
        # Convert the string to a list of dictionaries
        self.df['ingredients'] = self.df['ingredients'].apply(lambda ing: [eval(i.replace(']', '').replace('[', '')) for i in ing.split('\n')])

    def save(self):
        """Save the current DataFrame to the CSV file."""
        self.df.to_csv(RES_DATA_PATH, index=False)

    def filter(self, positive_products, negative_products):
        # Filter rows based on the ingredients column to include only recipes that
        # do not contain any negative products, sorted by the presence of positive products

        def contains_positive_products(ingredients):
            # Check if any ingredient matches any positive product
            ingredient_names = [item["name"].lower() for item in ingredients]
            return any(pos_prod.lower() in ingredient_names for pos_prod in positive_products)
        
        def contains_negative_products(i):
            # Check if any ingredient matches any negative product
            ingredients = i['ingredients']
            ingredient_names = [item["name"].lower() for item in ingredients]

            ing = any(neg_prod.lower() in ingredient_names for neg_prod in negative_products)
            steps = any(neg_prod.lower() in i['steps'] for neg_prod in negative_products)
            name = any(neg_prod.lower() in i['name'] for neg_prod in negative_products)

            return any([ing, steps, name])
        
        # Extract the ingredients column, filter, and sort
        filtered_df = self.df[~self.df.apply(contains_negative_products, axis=1)]
        if len(positive_products): 
            filtered_df = filtered_df[filtered_df['ingredients'].apply(contains_positive_products)]

        # Sort by the count of positive products in each recipe
        filtered_df = filtered_df.assign(
            positive_count=filtered_df['ingredients'].apply(
                lambda ingredients: sum(1 for ingredient in ingredients if ingredient["name"].lower() in positive_products)
            )
        ).sort_values(by='positive_count', ascending=False)

        # Drop the helper column used for sorting
        filtered_df = filtered_df.drop(columns=['positive_count'])

        return filtered_df

    def add(self, recipe):
        """
        Add a new recipe to the DataFrame and save changes to CSV.
        
        Parameters:
        recipe (dict): A dictionary containing the recipe information, with keys matching DataFrame columns.
        """
        new_recipe = pd.DataFrame([recipe])  # Convert the recipe dict to a DataFrame
        self.df = pd.concat([self.df, new_recipe], ignore_index=True)  # Append to the main DataFrame
        self.save()  # Save changes to CSV

    def update(self, recipe_name, updated_info):
        """
        Update an existing recipe based on the recipe name and save changes to CSV.
        
        Parameters:
        recipe_name (str): The name of the recipe to update.
        updated_info (dict): A dictionary containing the updated information for the recipe.
        """
        # Locate the recipe by name and update its details
        self.df.loc[self.df['name'] == recipe_name, updated_info.keys()] = updated_info.values()
        self.save()  # Save changes to CSV

    def delete(self, recipe_name):
        """
        Delete a recipe from the DataFrame based on the recipe name and save changes to CSV.
        
        Parameters:
        recipe_name (str): The name of the recipe to delete.
        """
        self.df = self.df[self.df['name'] != recipe_name]  # Filter out the recipe
        self.save()  # Save changes to CSV


# Run example
if __name__ == "__main__":
    # Initialize the RecipesStorage object
    recipes_storage = RecipesStorage()

    # Define positive and negative products to filter on
    positive_products = ["garlic", "onion", "ginger"]
    negative_products = ["sugar", "caraway seeds"]

    # Use the filter method to get the recipes that match the criteria
    filtered_recipes = recipes_storage.filter(positive_products, negative_products)
    print("Filtered Recipes:")
    print(filtered_recipes)
    
    # Example recipe to add
    new_recipe = {
        "name": "Garlic Ginger Soup",
        "review": "Excellent",
        "rating": 5,
        "meta": "healthy",
        "ingredients": [{"name": "garlic", "quantity": "3", "unit": "cloves"}, {"name": "ginger", "quantity": "1", "unit": "tbsp"}],
        "steps": "Mix all ingredients and cook.",
        "cooks_note": "Great for cold days.",
        "editors_note": "Best served hot.",
        "nutrition_facts": "Low calorie",
        "url": "http://example.com/garlic-ginger-soup"
    }
    
    # Add the new recipe
    recipes_storage.add(new_recipe)
    print("\nAfter Adding New Recipe:")
    print(recipes_storage.df.tail())

    # Update an existing recipe
    recipes_storage.update("Garlic Ginger Soup", {"rating": 4, "review": "Good"})
    print("\nAfter Updating Recipe:")
    print(recipes_storage.df[recipes_storage.df['name'] == "Garlic Ginger Soup"])

    # Delete a recipe by name
    recipes_storage.delete("Garlic Ginger Soup")
    print("\nAfter Deleting Recipe:")
    print(recipes_storage.df[recipes_storage.df['name'] == "Garlic Ginger Soup"])
