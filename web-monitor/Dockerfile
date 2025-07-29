FROM python:3-alpine

LABEL Description="Web Monitor"

RUN \
 apt-get update \
 && apt-get install --no-install-recommends --assume-yes \
  testssl.sh \
 && python3 -m venv /opt/python3-ven

COPY requirements.txt /
RUN /opt/python3-ven/bin/pip3 install -r requirements.txt

COPY *.py /

CMD /opt/python3-ven/bin/python3 /web-monitor.py /config/web-monitor.cfg
