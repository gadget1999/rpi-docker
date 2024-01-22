FROM gadget1999/rpi-python3:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Web Monitor"

RUN python3 -m venv /opt/python3-ven

COPY requirements.txt /
RUN /opt/python3-ven/bin/pip3 install -r requirements.txt

COPY *.py /

CMD /opt/python3-ven/bin/python3 /web-monitor.py /config/web-monitor.cfg
