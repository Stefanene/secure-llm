# secure-llm

This is the code repository for a CS350S final project at Stanford University written by Stefan Gabriel Ene. This project addresses the need for consumer confidentiality and privacy when prompting cloud-based LLMs. This is acheived through trusted execution environment and privacy-preserving techniques like ORAM, PIR, and private network access. More background can be found in the paper report of this methodology and its findings.

## How to Use
Clone this project using:
```
git clone https://github.com/Stefanene/secure-llm.git
```
Make sure you have Python3 your machine. This project was developed and tested on Python3.10.17.

To download all the dependencies, use the provieded `requirements.txt` file as such:
```
python3 -m pip install -r requirements.txt
```
Then, follow the setup guide below to deploy and use the system as currently built.

### 1. Setup Google Cloud Platform (GCP) locally
Download Google Cloud SDK as follows (for macOS):
```
brew install --cask google-cloud-sdk
```

Login into GCP account using:
```
gcloud auth login
```

Create a project on your GCP online interface. Then use that projects's `PROJECT_ID` to set the project workspace:
```
gcloud config set project PROJECT_ID
```

Optionally, check the list of available project as a sanity check using:
```
gcloud projects list
```

Finally, enable the required APIs:
```
gcloud services enable compute.googleapis.com
gcloud services enable confidentialcomputing.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

Now we can use the VM by running the `setup.sh` script, which will automatically SSH into the newly created VM on GCP!

### 2. Inside the VM
Run the setup script `gcp_setup.sh`.

Then add the server code located in `securellm_server.py`.

Set the API key using:
```
export GEMINI_API_KEY='your-key-here'
```

Now, you can run the Python script for the SecureLLM server using the provided execution script `run_server.sh`:
```
chmod +x run_server.sh
./run_server.sh
```

### 3. Back in the local terminal
Here, let's setup the client's endpoints. Run the `run_user.sh` script to setup the tunnel connetion on port 8080 using:
```
bash run_user.sh
```
Then, in another terminal we can run the python user code to communicate to the SecureLLM server:
```
python3.10 local_client.py
```

All done, we can enjoy sending secure LLM queries now!

### 4. Stopping the service
It is great practice to stop both listening port and the GCP confidential VM. Use CTRL+C/CMD+C to kill the tunnel connection process as well as the following command to stop the VM:
```
gcloud compute instances stop secure-llm-vm --zone=us-central1-a 
```

### 5. Re-running the process
Once the VM was exitted, you can reconnect to the VM to reuse this system using:
```
gcloud compute ssh secure-llm-vm --zone=us-central1-a --tunnel-through-iap
```
If needed, you can restart the VM using:
```
gcloud compute instances restart secure-llm-vm --zone=us-central1-a 
```

## Acknwledgements

This project was developed under the supervision of Dr. Emma Dauterman, as part of her CS350S Privacy-Preserving Systems seminar course at Stanford.