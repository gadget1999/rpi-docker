FROM gadget1999/rpi-alpine:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="FTP container for Raspberry Pi"

RUN apk --no-cache add vsftpd

COPY run.sh /bin/start_vsftpd.sh
RUN chmod u+x /bin/start_vsftpd.sh
COPY vsftpd.conf /etc/vsftpd/vsftpd.conf

EXPOSE 21 21000-21010

ENTRYPOINT ["/bin/start_vsftpd.sh"]
