FROM arm32v7/debian:buster-slim

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Debian image with Supervisor"

ARG TIMEZONE=America/New_York

RUN apt-get -y update && apt-get -y install htop nano supervisor && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

ADD ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
