FROM arm32v7/alpine:latest
COPY qemu-arm-static /usr/bin

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Alpine Linux image for Raspberry Pi"

ARG TIMEZONE=America/New_York

RUN apk add --update --no-cache bash tzdata htop nano && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \    
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

CMD ["sh"]
