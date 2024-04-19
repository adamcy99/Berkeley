#! /usr/bin/env bash

BUCKET="w261-final-hoky"
CLUSTER="hw5cluster"
PROJECT="w261-assignments"
JUPYTER_PORT="8123"
PORT="10000"
ZONE=$(gcloud config get-value compute/zone)


# CREATE SOCKS PROXY
gcloud compute ssh adamcy99@${CLUSTER}-m \
    --project=${PROJECT} \
    --zone=${ZONE}  \
    --ssh-flag="-D" \
    --ssh-flag=${PORT} \
    --ssh-flag="-N"

# DOCUMENTATION
# https://cloud.google.com/solutions/connecting-securely#socks-proxy-over-ssh
