import os
import time
import secrets
import json
import numpy as np
from flask import Flask, request, jsonify
from google import genai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

app = Flask(__name__)

# >>>>>>>>>>  PIR techniques helper <<<<<<<<<<

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


# >>>>>>>>>>  SecureLLM Server <<<<<<<<<<

class SecureLLMServer:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.query_counter = 0

        print("[SERVER] Initiliazed successfully")


    def anonymize_query(self, query: str):
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        print("[SERVER] Anonymizing query contents")
        analyzer_results = analyzer.analyze(text=query, language='en')
        anonymized_text = anonymizer.anonymize(text=query, analyzer_results=analyzer_results).text
        print("[SERVER] Query PII anonymized successfully")

        return anonymized_text
    

    def query_llm(self, query: str, anonymized: bool, use_oram: bool, use_pir: bool, use_delay: bool, num_dummies: int):
        print(f"\n[SERVER] Processing: '{query[:50]}'")

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
            print(f"[SERVER] Finalized request {i} out of {len(all_queries)}.")
        
        real_response = responses[real_idx] if real_idx < len(responses) else None

        print("\n[SERVER] Query complete\n")
        return real_response


# >>>>>>>>>>  initialize client <<<<<<<<<<

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

llm_server = SecureLLMServer(api_key=api_key)


# >>>>>>>>>>  API endpoints <<<<<<<<<<

@app.route('/health', methods=['GET'])
def health_check():
    return jasonify({"status": "healthy", "service": "SecureLLM"}), 200

@app.route('/query', methods=['POST'])
def query_endpoint():
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jasonify({"error": "Missing 'query' in request body"}), 400
        query = data['query']
        anonymized = data.get('anonymized', False)
        use_oram = data.get('use_oram', False)
        use_pir = data.get('use_pir', False)
        use_delay = data.get('use_delay', False)
        num_dummies = data.get('num_dummies', 0)
        
        start_time = time.perf_counter()
        response = llm_server.query_llm(
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
            return jasonify({"response": response.text, "execution_time": elapsed_time}), 200
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jasonify({"error": "No response from LLM"}), 500
    

# >>>>>>>>>>  main function <<<<<<<<<<

if __name__ == "__main__":
    print("[SERVER] Starting SecureLLM Server on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
