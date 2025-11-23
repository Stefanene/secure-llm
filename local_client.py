#!/usr/bin/env python3
"""
Local client to send queries to SecureLLM server on Confidential VM
"""

import requests
import json
import sys

class LocalSecureLLMClient:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        print(f"[CLIENT] Connected to: {self.server_url}")
    
    def health_check(self):
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                print("[CLIENT] ✓ Server is healthy")
                return True
            else:
                print(f"[CLIENT] ✗ Server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[CLIENT] ✗ Connection failed: {e}")
            return False
    
    def query(self, query: str, anonymized: bool = False, use_oram: bool = False, use_pir: bool = False, 
              use_delay: bool = False, num_dummies: int = 3):
        print(f"\n[LOCAL CLIENT] Sending query: '{query[:50]}...'")
        
        payload = {
            "query": query,
            "anonymized": anonymized,
            "use_oram": use_oram,
            "use_pir": use_pir,
            "use_delay": use_delay,
            "num_dummies": num_dummies
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/query",
                json=payload,
                timeout=120  # 2 minutes timeout for complex queries
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n[CLIENT] ✓ Response received")
                print(f"[CLIENT] Execution time: {data['execution_time']:.2f}s\n")
                return data['response']
            else:
                error_data = response.json()
                print(f"[CLIENT] ✗ Error: {error_data.get('error', 'Unknown error')}")
                return None
                
        except requests.exceptions.Timeout:
            print("[CLIENT] ✗ Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[CLIENT] ✗ Request failed: {e}")
            return None


def main():
    # connect to server through IAP tunnel
    client = LocalSecureLLMClient("http://localhost:8080")
    
    # check server health
    if not client.health_check():
        print("\n[ERROR] Cannot connect to server. Make sure:")
        print("  1. Server is running on the VM")
        print("  2. IAP tunnel is active:")
        print("     gcloud compute start-iap-tunnel secure-llm-vm 8080 --local-host-port=localhost:8080 --zone=us-central1-a")
        sys.exit(1)
    
    print("\nSecureLLM Local Client - Ready\n")
    
    queries = [
        {
            "query": "What are the differences between Intel SGX and TDX?",
            "anonymized": False,
            "use_oram": False,
            "use_pir": False,
            "use_delay": False,
            "num_dummies": 0
        }
    ]
    
    # run queries
    for i, q in enumerate(queries, 1):
        print(f"\n[CLIENT] Sending query {i}/{len(queries)}\n")
        response = client.query(**q)
        print(f"Response: {response[:200]}...\n")
    
    print("\n[CLIENT] All queries completed!")


if __name__ == "__main__":
    main()