FROM gadget1999/rpi-alpine

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Samba server for Raspberry Pi"

ARG TIMEZONE=America/New_York

# Install samba
RUN apk --no-cache --no-progress upgrade && \
    apk --no-cache --no-progress add su-exec samba && \
    rm -rf /var/cache/apk/* && \
    rm -rf /tmp/*
    
COPY run.sh /run.sh
RUN chmod u+x /run.sh

EXPOSE 10445 10137 10138 10139

ENTRYPOINT ["/run.sh"]
CMD ["-h"]
