FROM gadget1999/rpi-python3:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Weather station for Nook Simple Touch"

RUN pip3 install requests flask geopy

COPY server.py /
COPY static /static
COPY templates /templates

ENV GPS_COORDINATES=40.6976684,-74.2605725
ENV BIND_PORT=8080
# us = imperial units
ENV DARKSKY_API_UNITS=us
# en = english language
ENV DARKSKY_API_LANG=en

CMD python /server.py
