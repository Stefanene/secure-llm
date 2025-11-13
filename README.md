# secure-llm

This is the code repository for a CS350S final project at Stanford University written by Stefan Gabriel Ene. This project addresses the need for consumer confidentiality and privacy when prompting cloud-based LLMs. This is acheived through trusted execution environment and privacy-preserving techniques like ORAM, PIR, and anonymous computing. More background can be found in the paper report of this methodology and its findings.

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
Then, follow the setup guide below to deploy and use the model as currently built.

### 1. Setup Google Cloud Platform (GCP)
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

And check the list of available project using:
```
gcloud projects list
```

Finally, enable the required APIs:
```
gcloud services enable compute.googleapis.com
gcloud services enable confidentialcomputing.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

Now we can use the VM by running the `setup.sh` script!

### 2. Inside the VM

Run the setup script `gcp_setup.sh`.

Then add the client code located in `securellm.py`.

Set the API key using:
```
export GEMINI_API_KEY='your-key-here'
```

Now, you can run the Python script for the SecureLLM client using:
```
python3 securellm.py
```
Enjoy sending secure LLM queries!
<!-- Finally, run `run_secure_llm.sh`. -->

## Acknwledgements

This project was developed under the supervision of Dr. Emma Dauterman, as part of her CS350S Privacy-Preserving Systems seminar course at Stanford.