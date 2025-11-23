import os
import time
import secrets
import json
import numpy as np
from google import genai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


# >>>>>>>>>>  SecureLLM client <<<<<<<<<<

class PIRMethods:
    def pad_query(query: str, target_length: int = 500):
        if len(query) < target_length:
            return query + ' ' * (target_length - len(query))
        
        return query[:target_length]
    
    def add_dummy_queries(real_query: str, num_dummies: int = 3):
        dummies = [
            "What is the weather today?",
            "Tell me a fun fact about cryptography.",
            "Explain machine learning basics.",
            "What are the benefits of privacy?",
            "Describe cyptography.",
            "What is a trusted execution enviroment?",
            "How does cryptography work?",
            "What is quantum computing?",
        ]
        selected = secrets.SystemRandom().sample(dummies, min(num_dummies, len(dummies)))
        all_queries = selected[:]
        insert_pos = secrets.randbelow(len(all_queries) + 1)
        all_queries.insert(insert_pos, real_query)
        
        return all_queries, insert_pos


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
    

    def query_llm(self, query: str, anonymized: bool, use_oram: bool, use_pir: bool, use_delay: bool, num_dummies: int):
        print(f"\n[CLIENT] Processing: '{query[:50]}'")

        client = genai.Client(api_key=self.api_key)

        if (anonymized):
            processed_query = self.anonymize_query(query=query)
            query = processed_query

        if use_pir:
            padded_query = PIRMethods.pad_query(query, target_length=200)
            all_queries, real_idx = PIRMethods.add_dummy_queries(padded_query, num_dummies)
            print(f"\n[PIR] Promping {len(all_queries)} queries (real at index {real_idx})")
        else:
            all_queries = [query]
            real_idx = 0

        responses = []
        for i, q in enumerate(all_queries):
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=q,
            )

            if use_delay and i < len(all_queries) - 1:
                delay = secrets.randbelow(2000) / 1000.0 + 0.5
                time.sleep(delay)

            responses.append(response)
            print(f"[CLIENT] Finalized request {i} out of {len(all_queries)}.")
        
        real_response = responses[real_idx] if real_idx < len(responses) else None

        print("\n[CLIENT] Query complete\n")
        return real_response


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
        use_delay=False,
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