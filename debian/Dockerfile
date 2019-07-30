FROM arm32v7/debian:buster-slim

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Debian image with Supervisor"

ARG TIMEZONE=America/New_York

RUN apt-get -y update && apt-get -y install \
    # docker specific
    supervisor cron \
    # base packages
    curl deborphan htop mc nano ncdu p7zip screen sudo wget unzip \
    # mqtt, firebase, acme.sh, ddns
    dnsutils jq mosquitto-clients socat \
    # pyload, pyby, pybox
    python python-requests python-poster python-mechanize python-openssl \    
    && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

ADD ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf
ADD ./get-cmds.sh /usr/local/bin/get-cmds.sh
RUN chmod +x /usr/local/bin/get-cmds.sh

CMD ["/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
