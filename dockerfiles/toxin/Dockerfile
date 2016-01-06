FROM ubuntu:14.04
MAINTAINER HPN ASIC API Team "hpe-networking@lists.hp.com"

# Make sure you have an updated version of txn and txnd available for docker.
# You can get them from:
#     https://github.com/HPNetworking/hpe-networking/txn
#     https://github.com/HPNetworking/hpe-networking/txnd
# Change this when txn and txnd are on PyPI
ADD txnd /tmp/txnd
ADD txn /tmp/txn

RUN apt-get update && \
    apt-get --yes install python-pip python-dev libpcap-dev git && \
    pip install -e git+https://github.com/jnthntatum/pcapy.git@feature/python3-support#egg=pcapy-0.10.9 && \
    pip install /tmp/txnd && \
    pip install /tmp/txn && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
