
def get_prompt(context):
    prompt = f"""
        Your task is to find university institute location where Andrzej Maj worked, based on below context and your base knowledge.
        
        Rules:
        - In below context you have information about Andrzej Maj from several people.
        - Think out loud(in polish) about your task and steps in the "_thinking" field
         
        Steps:
        - In below context find information about university institute where Andrzej Maj worked.
        - In your base knowledge find university institute location
        - return location street name in street field
        
        Response in json format:
        {{"_thinking":"", street:"street name"}}
        
        context
        ###
        {context}
        ###
        """
    return prompt
