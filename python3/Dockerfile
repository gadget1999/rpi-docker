FROM gadget1999/rpi-alpine:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Python3 container for Raspberry Pi"

RUN apk add --update --no-cache python3 && \
    pip3 install --upgrade pip && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

CMD ["sh"]
