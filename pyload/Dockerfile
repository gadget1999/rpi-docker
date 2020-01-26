FROM gadget1999/rpi-python2:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Pyload for Raspberry Pi"

RUN apk add --no-cache \
	 curl sqlite unrar unzip \
	 py-curl py-imaging py2-crypto py2-openssl \
	&& \
    mkdir -p /app/pyload && \
	curl -o /tmp/pyload.tar.gz -L \
	 "https://github.com/pyload/pyload/archive/v0.4.9.tar.gz" && \
	tar xf /tmp/pyload.tar.gz -C \
	 /app/pyload --strip-components=1 && \
	echo "/config" > /app/pyload/module/config/configdir && \
	rm -rf /root/.cache /tmp/* /var/tmp/* /var/cache/apk/*

COPY pyload.conf /

CMD python /app/pyload/pyLoadCore.py
