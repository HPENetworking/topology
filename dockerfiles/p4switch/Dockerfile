FROM      ubuntu:14.04
MAINTAINER HPN ASIC API Team "hpe-networking@lists.hp.com"

RUN apt-get update ; \
    apt-get install -y \
    automake \
    bridge-utils \
    build-essential \
    ethtool \
    git \
    libboost-dev \
    libboost-filesystem-dev \
    libboost-program-options-dev \
    libboost-system-dev \
    libboost-test-dev \
    libedit-dev \
    libevent-dev \
    libglib2.0-dev \
    libhiredis-dev \
    libjudy-dev \
    libnl-route-3-dev \
    libpcap0.8 \
    libpcap0.8-dev \
    libtool \
    libssl-dev \
    libgmp-dev \
    openssh-server \
    openssh-client \
    packit \
    pkg-config \
    python-dev \
    python-pygraph \
    python-pygraphviz \
    python-setuptools \
    python-thrift \
    python-yaml \
    quagga \
    redis-server \
    redis-tools \
    subversion \
    tshark \
    xterm

# install thrift
RUN mkdir -p /tmp/thrift ; \
    cd /tmp/thrift ; \
    wget -q http://archive.apache.org/dist/thrift/0.9.2/thrift-0.9.2.tar.gz ; \
    tar xvzf thrift-0.9.2.tar.gz; \
    cd thrift-0.9.2; \
    ./configure ; cd test/cpp ; ln -s . .libs ; cd ../.. ; \
    make -j 4 install; ldconfig ; \
    rm -fr /tmp/thrift

# install scapy
RUN mkdir -p /tmp/scapy ; \
    cd /tmp/scapy ; \
    git clone https://github.com/p4lang/scapy-vxlan.git ; \
    cd scapy-vxlan ; \
    python setup.py install ; \
    rm -fr /tmp/scapy

# install p4-hlir
RUN mkdir -p /tmp/p4-hlir ; \
    cd /tmp/p4-hlir ; \
    git clone https://github.com/p4lang/p4-hlir.git ; \
    cd p4-hlir ; \
    python setup.py install ; \
    rm -fr /tmp/p4-hlir

# install ctypesgen
RUN mkdir -p /tmp/ctypesgen ; \
    cd /tmp/ctypesgen ; \
    git clone https://github.com/davidjamesca/ctypesgen.git ; \
    cd ctypesgen ; \
    python setup.py install ; \
    rm -fr /tmp/ctypesgen

RUN mkdir -p /tmp/libnanomsg ; \
    cd /tmp/libnanomsg ; \
    wget -c http://download.nanomsg.org/nanomsg-0.5-beta.tar.gz ; \
    tar zxvf nanomsg-0.5-beta.tar.gz ; \
    cd nanomsg-0.5-beta ; \
    ./configure ; \
    make -j4 ; \
    sudo make install ; \
    sudo ldconfig ; \
    rm -fr /tmp/libnanomsg

RUN eval $(ssh-agent -s) ; \
    ssh-add /home/root/.ssh/id_rsz ; \
    ssh -o StrictHostKeyChecking=no git@github.com uptime ; \
    ssh -T git@github.com ; \
    cd / ; \
    git clone https://github.com/p4lang/p4factory.git p4factory ; \
    cd /p4factory ; \
    git submodule update --init --recursive ; \
    ./autogen.sh ; \
    ./configure ; \
    cd /p4factory/targets/switch ; \
    make -j4 bm

# install mstpd
RUN mkdir -p /third-party/diffs ; \
    cp /p4factory/docker/diffs/mstpd.diff /third-party/diffs/mstpd.diff ; \
    cd /third-party ; \
    svn checkout http://svn.code.sf.net/p/mstpd/code/trunk mstpd ; \
    cd mstpd; patch -p0 -i /third-party/diffs/mstpd.diff; make install

ENV VTYSH_PAGER more
