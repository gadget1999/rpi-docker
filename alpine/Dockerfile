FROM arm32v6/alpine:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Alpine image for Raspberry Pi"

ARG TIMEZONE=America/New_York

COPY qemu-arm-static /usr/bin/qemu-arm-static

RUN apk add --update --no-cache bash tzdata htop nano && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \    
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

CMD ["sh"]
