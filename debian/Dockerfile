FROM arm32v7/debian:buster-slim

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Debian image with Cron"

ARG TIMEZONE=America/New_York

RUN apt-get -y update && apt-get -y install \
    # docker specific
    cron \
    # base packages
    htop nano procps wget unzip \
    # mqtt, firebase, acme.sh, ddns
#    curl dnsutils jq mosquitto-clients socat \
    && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

ADD ./entrypoint /entrypoint
ADD ./init-cmds /usr/local/bin/init-cmds

RUN chmod +x /entrypoint /usr/local/bin/init-cmds && \
	/usr/local/bin/init-cmds

CMD ["/entrypoint"]