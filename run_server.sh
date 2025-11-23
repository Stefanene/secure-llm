#!/bin/bash

# final checks
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY not set"
    echo "Usage: export GEMINI_API_KEY='your-key' && ./run_llm.sh"
    exit 1
fi

# begin client execution
cd ~/secure-llm-gcp
source venv/bin/activate

python3 securellm_server.py
