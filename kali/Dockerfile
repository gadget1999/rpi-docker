FROM kalilinux/kali-linux-docker

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Kali Linux in a container"

ARG TIMEZONE=America/New_York

RUN apt-get -y update && \
	apt-get -y full-upgrade && \
	apt-get -y install \
	kali-linux-top10 kali-linux-web man-db exploitdb
    && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \
	apt-get autoremove && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

ADD ./.bash_profile /root/.bash_profile

CMD ["/bin/bash", "-c", "cd"]

