FROM arm32v7/debian:buster-slim

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Debian image with Supervisor"

ARG TIMEZONE=America/New_York

RUN apt-get -y update && apt-get -y install \
    # docker specific
    cron \
    # base packages
    htop nano wget unzip \
    # mqtt, firebase, acme.sh, ddns
#    curl dnsutils jq mosquitto-clients socat \
    && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

ADD ./entrypoint.sh /user/local/bin/entrypoint.sh
ADD ./get-cmds.sh /usr/local/bin/get-cmds.sh
RUN chmod +x /user/local/bin/entrypoint.sh /usr/local/bin/get-cmds.sh

CMD ["/usr/local/bin/entrypoint.sh"]
