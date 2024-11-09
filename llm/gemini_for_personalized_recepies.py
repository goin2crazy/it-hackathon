from .gemini_inference import GeminiInference

# New custom class for personalized recipes based on GeminiInference
class GeminiForPersonalizedRecipes(GeminiInference): 
    def prompt(self, user_params, recepy_params): 
        positive_products = user_params.get("positive_products", "")
        negative_products = user_params.get("negative_products", "")
        specific_diet = user_params.get("specific_diet", "")
        chronic_illnesses = user_params.get("chronic_illnesses", "")



        return f"""
        Hello, I need help creating a list of rewrite the recipe to more comfortable for me. Here is some important information about me:
        
        - products I prefer: {positive_products}
        - Ingredients i have allelgic on: {negative_products}
        - Specific diet type: {specific_diet}
        - Chronic illnesses or conditions: {chronic_illnesses}

        The recipe params i need to be personalized for me: 
        {recepy_params}
        
        Please generate a recipe suggestion that matches my preferences and health conditions. If relevant, consider health conditions like diabetes or heart health and make recommendations accordingly.
        
        Format the output as JSON with each recipe including:
        
        <start>
        {{
            "recipe_name": "Recipe Name",
            "ingredients": ["Ingredient1", "Ingredient2", ...],
            "instructions": "Step-by-step cooking instructions."
        }}
        <end>
        
        Only output the JSON within <start> and <end> tags.
        if you dont know or dont have enough information please just answer with standart and healthy meal plan
        """

    def extract_target_answer(self, response): 
        """
        Custom method to process the model's output.
        It extracts the JSON data enclosed within <start> and <end> tags.
        """
        # try: 
        start_tag = "<start>"
        end_tag = "<end>"
        
        # Extract the JSON content between tags
        extracted_content = response.split(start_tag)[-1]
        extracted_content = extracted_content.split(end_tag)[0]

        extracted_content  = extracted_content.split("</start>")[-1]
        extracted_content  = extracted_content.split("</end>")[0]
        return eval(extracted_content)
        # except:
            # Handle case where tags are missing or malformed response
            # print( {"error": "Response format is incorrect or tags are missing"})
            # return response
    

