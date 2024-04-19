#! /usr/bin/env bash

BUCKET="w261-final-hoky"
CLUSTER="hw5cluster"
PROJECT="w261-assignments"
JUPYTER_PORT="8123"
PORT="10000"
ZONE='us-west1-b' #(gcloud config get-value compute/zone)


# USE SOCKS PROXY
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --proxy-server="socks5://localhost:${PORT}" \
  --user-data-dir=/tmp/${CLUSTER}-m


# DOCUMENTATION
# https://cloud.google.com/solutions/connecting-securely#socks-proxy-over-ssh
