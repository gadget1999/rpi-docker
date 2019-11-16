FROM debian:stretch-slim

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Build environment for RT-N56U firmware"

RUN apt-get clean all && \
    apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install  build-essential \
                        gawk \
                        pkg-config \
                        gettext \
                        automake \
                        autogen \
                        texinfo \
                        autoconf \
                        libtool \
                        bison \
                        flex \
                        zlib1g-dev \
                        libgmp3-dev \
                        libmpfr-dev \
                        libmpc-dev \
                        kmod \
                        sudo \
                        vim && \
    apt-get -y purge manpages \
                     xauth \
                     debconf-i18n && \
    apt-get -y autoremove && \
    apt-get -y autoclean && \
    apt-get clean all && \
    mkdir /opt/rt-n56u

WORKDIR /opt/rt-n56u/trunk
