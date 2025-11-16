FROM gadget1999/rpi-python3:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Media processing tool"

COPY requirements.txt /
RUN \
    /opt/python3-ven/bin/pip3 install -r requirements.txt

COPY *.py /
COPY config /config
COPY media /media
COPY utils /utils
