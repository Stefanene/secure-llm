#!/bin/bash

# Create C3 VM with Intel TDX

# set variables; add personal project ID below
export PROJECT_ID="ADD_PROJECT_ID_HERE"
export VM_NAME="confidential-llm-vm"
export ZONE="us-central1-a"
export MACHINE_TYPE="c3-standard-4"

# create firewall rules
gcloud compute firewall-rules create allow-ssh \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0


# create VM
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --confidential-compute-type=TDX \
    --maintenance-policy=TERMINATE \
    --boot-disk-size=50GB \
    --tags=allow-ssh

# connect to VM
gcloud compute ssh $VM_NAME --zone=$ZONE

# # ================================================
# # Commands for future uses:

# # stop the VM
# gcloud compute compute instances stop confidential-llm-vm --zone=us-central1-a

# # restart the to VM
# gcloud compute compute instances reset confidential-llm-vm --zone=us-central1-a

# # connect back toto VM
# gcloud compute ssh confidential-llm-vm --zone=us-central1-a
