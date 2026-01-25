import asyncio
import ollama
import json

async def run_test():
    system_prompt = """
        You are a helpful bilingual language tutor (Portuguese/English).
        Valid JSON Output is MANDATORY.
        Root element must be a JSON ARRAY.
        
        Instructions:
        - If the user asks for a phrase, generate a creative one.
        - If the user asks for a translation, provide the translation.
        - If the user asks for the same phrase in both languages, provide two segments.
        
        Output Format:
        [
            {"text": "Portuguese text here", "lang": "pt"},
            {"text": "English text here", "lang": "en"}
        ]
        
        Do not output any markdown or conversational text outside the JSON.
    """
    
    user_input = "me fale uma frase em portugues e a mesma frase em ingles"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    client = ollama.AsyncClient()
    
    print(f"Sending request to Ollama (model: mistral)...")
    try:
        response = await client.chat(model="mistral", messages=messages, format="json")
        content = response['message']['content']
        print(f"Raw Response Content: '{content}'")
        
        try:
            parsed = json.loads(content)
            print(f"Parsed JSON: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
            
            segments = parsed
            if isinstance(segments, dict):
                 for key in ['data', 'segments', 'items', 'response']:
                     if key in segments and isinstance(segments[key], list):
                         segments = segments[key]
                         break
                 else:
                     segments = [segments]
            
            if isinstance(segments, dict):
                segments = [segments]
            
            ai_text = " ".join([seg.get("text", "") for seg in segments])
            print(f"Derived AI Text: '{ai_text}'")
            
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            
    except Exception as e:
        print(f"Ollama Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
