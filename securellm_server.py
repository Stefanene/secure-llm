# SecureLLM server on Confidential VM

import os
import time
import secrets
import json
import numpy as np
from flask import Flask, request, jsonify
from dataclasses import dataclass
from google import genai
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding
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


# >>>>>>>>>>  Path ORAM <<<<<<<<<<

@dataclass
class ORAMBlock:
    block_id: int
    data: bytes
    leaf_id: int


class SimpleORAM:
    
    def __init__(self, num_blocks: int = 128, block_size: int = 2048):
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.tree_height = int(np.ceil(np.log2(num_blocks))) + 1
        self.num_leaves = 2 ** (self.tree_height - 1)
        
        self.position_map = {}
        self.storage = {}
        self.stash = []
        print(f"[SERVER] ORAM initialized with: {num_blocks} blocks, tree height {self.tree_height}")

    def _assign_random_leaf(self):
        return secrets.randbelow(self.num_leaves)
    
    def _read_path(self, leaf_id: int):
        path_blocks = []
        for block_id, stored_leaf in self.position_map.items():
            if stored_leaf == leaf_id and block_id in self.storage:
                path_blocks.append(self.storage[block_id])
        return path_blocks
    
    def _writeback_path(self, leaf_id: int):
        blocks_to_write = [b for b in self.stash if b.leaf_id == leaf_id]
        for block in blocks_to_write:
            self.storage[block.block_id] = block
            self.stash.remove(block)

    def oblivious_write(self, block_id: int, data: bytes):
        if len(data) < self.block_size:
            data = data + b'\00' * (self.block_size - len(data))
        elif len(data) > self.block_size:
            data = data[:self.block_size]

        leaf_id = self._assign_random_leaf()
        self.position_map[block_id] = leaf_id

        block = ORAMBlock(block_id=block_id, data=data, leaf_id=leaf_id)
        self.stash.append(block)
        self._writeback_path(leaf_id)

    def oblivious_read(self, block_id: int):
        leaf_id = self.position_map.get(block_id, self._assign_random_leaf())
        path_blocks = self._read_path(leaf_id)

        target_data = None
        for block in path_blocks + self.stash:
            if block.block_id == block_id:
                target_data = block.data
                new_leaf = self._assign_random_leaf()
                self.position_map[block_id] = new_leaf
                block.leaf_id = new_leaf
                break
        
        self._writeback_path(leaf_id)
        return target_data if target_data else b''



# >>>>>>>>>>  SecureLLM Server <<<<<<<<<<

class SecureLLMServer:

    def __init__(self, api_key: str):
        self.api_key = api_key

        self.query_counter = 0

        self.memory_key = secrets.token_bytes(32)

        print("[SERVER] Initiliazed successfully")
        self.oram = SimpleORAM(num_blocks=128, block_size=2048)

    def _encrypt_memory(self, data: bytes):
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(self.memory_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return iv + ciphertext
    
    def _decrypt_memory(self, encrypted_data: bytes):
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]

        cipher = Cipher(algorithms.AES(self.memory_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = sym_padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data

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

        if use_oram:
            query_id = self.query_counter
            self.query_counter += 1
        
            encrypted_query = self._encrypt_memory(query.encode('utf-8'))
            self.oram.oblivious_write(query_id, encrypted_query)
            print(f"[SERVER] Query stored in ORAM (ID: {query_id})")

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
            print(f"[SERVER] Finalized request {i+1} out of {len(all_queries)}.")
        
        real_response = responses[real_idx] if real_idx < len(responses) else None

        if use_oram:
            response_str = real_response.text
            encrypted_response = self._encrypt_memory(response_str.encode('utf-8'))
            self.oram.oblivious_write(query_id+1000, encrypted_response)
            print(f"[SERVER] Response stored in ORAM (ID: {query_id+1000})")


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
    return jsonify({"status": "healthy", "service": "SecureLLM"}), 200

@app.route('/query', methods=['POST'])
def query_endpoint():
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        query = data['query']
        anonymized = data.get('anonymized')
        use_oram = data.get('use_oram')
        use_pir = data.get('use_pir')
        use_delay = data.get('use_delay')
        num_dummies = data.get('num_dummies')
        
        start_time = time.perf_counter()
        response = llm_server.query_llm(
            query=query,
            anonymized=anonymized,
            use_oram=use_oram,
            use_pir=use_pir,
            use_delay=use_delay,
            num_dummies=num_dummies
        )
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        if response:
            return jsonify({"response": response.text, "execution_time": elapsed_time}), 200
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": "No response from LLM"}), 500
    

# >>>>>>>>>>  main function <<<<<<<<<<

if __name__ == "__main__":
    print("[SERVER] Starting SecureLLM Server on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
