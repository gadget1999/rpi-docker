FROM kalilinux/kali-linux-docker

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Kali Linux in a container"

ARG TIMEZONE=America/New_York

RUN apt-get -y update && \
	apt-get -y full-upgrade && \
	apt-get -y install \
	kali-linux-top10 kali-linux-web man-db exploitdb htop \
    && \
    cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime && echo "${TIMEZONE}" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

ADD ./init-cmds /usr/local/bin/init-cmds

RUN chmod +x /usr/local/bin/init-cmds && \
	/usr/local/bin/init-cmds

CMD ["/bin/bash", "-c", "cd; /bin/bash -l"]