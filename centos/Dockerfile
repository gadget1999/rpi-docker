FROM centos:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Base Debian image with Supervisor"

ARG TIMEZONE=America/New_York

RUN yum -y update && \
    # EPEL repository
    yum -y install epel-release && \
    yum -y install \
    # Base packages
    supervisor cronie htop nano unzip wget \
    && \
    yum clean all

ADD ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf
ADD ./get-cmds.sh /usr/local/bin/get-cmds.sh
RUN chmod +x /usr/local/bin/get-cmds.sh

CMD ["/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
