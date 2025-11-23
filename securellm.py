import os
import time
import time
import json
import numpy as np
from google import genai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


# >>>>>>>>>>  SecureLLM client <<<<<<<<<<

class SecureLLMClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.query_counter = 0

        print("[CLIENT] Initiliazed successfully")


    def anonymize_query(self, query: str):
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        print("[CLIENT] Anonymizing query contents")
        analyzer_results = analyzer.analyze(text=query, language='en')
        anonymized_text = anonymizer.anonymize(text=query, analyzer_results=analyzer_results).text
        print("[CLIENT] Query PII anonymized successfully")

        return anonymized_text
    

    def query_llm(self, query: str, anonymized: bool, use_oram: bool, use_pir: bool, num_dummies: int):
        print(f"\n[CLIENT] Processing: '{query[:50]}'")

        client = genai.Client(api_key=self.api_key)

        if (anonymized):
            processed_query = self.anonymize_query(query=query)
            query = processed_query

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

    start_time = time.perf_counter()
    response = client.query_llm(
        query=query,
        anonymized=False,
        use_oram=False,
        use_pir=False,
        num_dummies=0
    )
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    if response:
        text = response.text
        print(f"Response: {text[:200]}...\n")
   
    print(f"[CLIENT] Execution time: {elapsed_time:.6f} seconds")

if __name__ == "__main__":
    main()