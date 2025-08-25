ARG TARGET_PLATFORM
FROM debian:bookworm-slim

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Weather station for Kindle"

COPY requirements.txt /

RUN apt-get -y update && apt-get -y install \
    python3 py3-pip py3-virtualenv wkhtmltopdf && \
    python3 -m venv /opt/python3-ven && \
    /opt/python3-ven/bin/pip3 install --upgrade pip && \
    /opt/python3-ven/bin/pip3 install -r requirements.txt && \
    apt-get clean && \  
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

COPY *.py /
COPY weather /weather
COPY misc /misc
COPY static /static
COPY templates /templates

ENV GPS_COORDINATES=40.6976684,-74.2605725
ENV BIND_PORT=8080

CMD ["/opt/python3-ven/bin/python3", "/server.py"]
