from .gemini_inference import GeminiInference

class GeminiForMealPlanGeneration(GeminiInference): 
    def prompt(self, user_params): 
        health_and_diet = '{' + '\n'.join("{k}: {v}" for k, v in user_params.items()) + "}"
        return f"""
        Hi, I'd like your help generating a personalized meal plan. Here are my diet and health parameters:
        {health_and_diet}

        Please create a meal plan that includes "breakfast," "lunch," and "dinner" with specific dish names, ingredients, and portion sizes for each meal. 
        If possible, consider nutrient balance (carbs, protein, fats) and avoid ingredients that might conflict with my diet and health restrictions.

        Please return the result in JSON format, strictly structured as follows:

        <start>
        {{
            "meal_plan": {{
                "breakfast": {{
                    "dish_name": "Example Dish",
                    "ingredients": ["Ingredient1", "Ingredient2", ...],
                    "portion_size": "Example portion size"
                }},
                "lunch": {{
                    "dish_name": "Example Dish",
                    "ingredients": ["Ingredient1", "Ingredient2", ...],
                    "portion_size": "Example portion size"
                }},
                "dinner": {{
                    "dish_name": "Example Dish",
                    "ingredients": ["Ingredient1", "Ingredient2", ...],
                    "portion_size": "Example portion size"
                }}
            }}
        }}
        <end>

        Only output the JSON within <start> and <end> tags. Thank you!
        if you dont know or dont have enough information please just answer with standart and healthy meal plan
        """

    
    def extract_target_answer(self, response): 
        """
        Custom method to process the model's output.
        It extracts the JSON data enclosed within <start> and <end> tags.
        """
        start_tag = "<start>"
        end_tag = "<end>"
        
        start_index = response.find(start_tag)
        end_index = response.find(end_tag, start_index)
        
        # Check if both tags are found
        if start_index != -1 and end_index != -1:
            # Extract the JSON content between tags
            extracted_content = response[start_index + len(start_tag):end_index].strip()
            return eval(extracted_content)
        else:
            # Handle case where tags are missing or malformed response
            print( {"error": "Response format is incorrect or tags are missing"})
            return response
    
