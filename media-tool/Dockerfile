FROM gadget1999/rpi-python3:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Media processing tool"

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN /opt/python3-ven/bin/pip3 install -r requirements.txt

COPY *.py /
COPY config /config
COPY media /media
COPY utils /utils

ENV MEDIA_TOOL_CONFIG=/config/config.yaml

ENTRYPOINT ["/opt/python3-ven/bin/python3", "/main.py", "/config/config.yaml"]
