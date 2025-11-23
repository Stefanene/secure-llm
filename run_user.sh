#!/bin/bash

# Run the SecureLLM local client code

echo ""
echo "Run in another terminal: python3 local_client.py"
echo ""


gcloud compute start-iap-tunnel secure-llm-vm 8080 \
    --local-host-port=localhost:8080 \
    --zone=us-central1-a