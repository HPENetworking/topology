FROM ubuntu:14.04
MAINTAINER HPN ASIC API Team "hpe-networking@lists.hp.com"

RUN apt-get update ; \
    apt-get install -y --no-install-recommends \
    python-setuptools \
    python-pip \
    python-eventlet \
    python-lxml \
    python-msgpack \
    unzip \
    wget ; \
    rm -rf /var/lib/apt/lists/*

ENV HOME /root
WORKDIR /root

RUN pip install supervisor supervisor-stdout --pre ; \
    mkdir -p /var/log/supervisor/

RUN wget --no-check-certificate https://github.com/osrg/ryu/archive/master.zip ; \
    unzip master.zip ; \
    cd ryu-master ; \
    pip install -r tools/pip-requires ; \
    python setup.py install

ADD supervisord.conf /etc/
