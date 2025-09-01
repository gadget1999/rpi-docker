FROM gadget1999/rpi-python3:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Weather station for Nook Simple Touch"

COPY requirements.txt /
RUN apk add --no-cache \
      cairo pango gdk-pixbuf ttf-dejavu font-wqy-zenhei && \
    apk add --no-cache --virtual .build-deps \
      build-base cairo-dev musl-dev python3-dev libffi-dev && \
    /opt/python3-ven/bin/pip3 install -r requirements.txt && \
    apk del .build-deps

COPY *.py /
COPY weather /weather
COPY misc /misc
COPY static /static
COPY templates /templates
COPY quotes /quotes

ENV GPS_COORDINATES=40.6976684,-74.2605725
ENV BIND_PORT=8080

CMD ["/opt/python3-ven/bin/python3", "/server.py"]
