FROM gadget1999/rpi-alpine:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Python2 container for Raspberry Pi"

RUN apk add --no-cache python && \
    python -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip install --upgrade pip setuptools && \
    rm -rf /root/.cache /tmp/* /var/tmp/* /var/cache/apk/*

CMD ["sh"]
