import os
import time
import json
import numpy as np
from google import genai


# >>>>>>>>>>  SecureLLM client <<<<<<<<<<

class SecureLLMClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.query_counter = 0

        print("[CLIENT] Initiliazed successfully")

    def query_llm(self, query: str, use_pir: bool, anonymous: bool, num_dummies: int):
        print(f"\n[CLIENT] Processing: '{query[:50]}'")

        client = genai.Client(api_key=self.api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=query,
        )
        
        print("[CLIENT] Query complete\n")
        return response


# >>>>>>>>>>  main functions <<<<<<<<<<

def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("[ERROR]: GEMINI_API_KEY environment variable not set")
        print("\tSet it with: export GEMINI_API_KEY='your-key-here'")
        return
    
    client = SecureLLMClient(api_key=api_key)

    query = "What are the differences between Intel SGX and TDX"

    response = client.query_llm(query=query, use_pir=True, anonymous=True, num_dummies=3)

    if response:
        text = response.text
        print(f"Response: {text[:200]}...\n")


if __name__ == "__main__":
    main()