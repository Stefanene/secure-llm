import os
import time
import json
import numpy as np
import requests
from google import genai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


# >>>>>>>>>>  Tor network anonymizer <<<<<<<<<<
class TorAnonymizer:
    def __init__(self, socks_port: int = 9050, ctrl_port: int = 9051):
        self.socks_port = socks_port
        self.ctrl_port = ctrl_port
        self.proxies = {
            'http':f'socks5h://127.0.0.1:{socks_port}',
            'https':f'socks5h://127.0.0.1:{socks_port}'
        }
        self.session = requests.Session()
        self.session.proxies.update(self.proxies)

        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0',
        ]



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

    def query_llm(self, query: str, use_pir: bool, anonymous: bool, num_dummies: int):
        print(f"\n[CLIENT] Processing: '{query[:50]}'")

        client = genai.Client(api_key=self.api_key)

        processed_query = self.anonymize_query(query=query)

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=processed_query,
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