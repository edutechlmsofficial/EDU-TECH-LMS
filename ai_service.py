import os
from dotenv import load_dotenv

load_dotenv()

# Check if OpenAI API key is available
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
else:
    client = None

def get_ai_tutor_response(query: str) -> str:
    if client is None:
        return "AI tutor service is currently unavailable. Please ensure the OpenAI API key is configured."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI tutor for educational purposes. Provide helpful, accurate, and engaging responses to student queries."},
                {"role": "user", "content": query}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def generate_content(topic: str) -> str:
    if client is None:
        return "AI content generation service is currently unavailable. Please ensure the OpenAI API key is configured."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI content generator for educational materials. Create engaging and informative content on the given topic."},
                {"role": "user", "content": f"Generate educational content about: {topic}"}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"
