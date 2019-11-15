# Build me with:
#
#    docker build \
#       --build-arg http_proxy=${http_proxy} \
#       --build-arg https_proxy=${https_proxy} \
#       -t topology/host:latest .

FROM ubuntu:16.04
MAINTAINER Hewlett Packard Enterprise Development LP "hpe-networking@lists.hp.com"


# Set the locale
ENV LANG en_US.UTF-8
RUN locale-gen en_US.UTF-8 && update-locale LANG=en_US.UTF-8


# Install base system software
RUN apt-get update && apt-get --yes --no-install-recommends install \
        ca-certificates curl python3 && \
    apt-get clean


# Install networking software
RUN apt-get --yes --no-install-recommends install \
        iproute2 \
        iperf \
        tcpdump \
        iputils-ping \
        iputils-arping \
        iputils-tracepath \
        dnsutils \
        openssh-client \
        ostinato && \
    apt-get clean


# Install Python modules
RUN curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    python3 /tmp/get-pip.py && \
    rm /tmp/get-pip.py && \
    pip3 install \
        scapy-python3
