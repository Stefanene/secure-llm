#!/bin/bash

# Create C3 VM with Intel TDX

# set variables; add personal project ID below
export PROJECT_ID="ADD_PROJECT_ID_HERE"
export VM_NAME="secure-llm-vm"
export ZONE="us-central1-a"
export REGION="us-central1"
export MACHINE_TYPE="c3-standard-4"

# enable Google's private network
gcloud compute networks subnets update default \
    --region=$REGION \
    --enable-private-ip-google-access

# create firewall rules for IAP (Identity-Aware Proxy) SSH access
gcloud compute firewall-rules create allow-iap-ssh \
    --allow=tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --network=default \
    --direction=INGRESS

# create VM with no external IP
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --confidential-compute-type=TDX \
    --maintenance-policy=TERMINATE \
    --boot-disk-size=50GB \
    --no-address \
    --tags=allow-iap-ssh

echo "VM created with private network access only"
echo "Connecting via Identity-Aware Proxy..."

# connect to VM
gcloud compute ssh $VM_NAME \
    --zone=$ZONE \
    --tunnel-through-iap

# # ================================================
# # Commands for future uses:

# # stop the VM
# gcloud compute compute instances stop secure-llm-vm --zone=us-central1-a

# # restart the to VM
# gcloud compute compute instances reset secure-llm-vm --zone=us-central1-a

# # connect back toto VM
# gcloud compute ssh secure-llm-vm --zone=us-central1-a
