FROM debian:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Debian image with Supervisor"

ARG TIMEZONE=America/New_York

RUN apt-get --update --no-cache htop nano supervisor && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \    
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

CMD ["/usr/bin/supervisord"]
