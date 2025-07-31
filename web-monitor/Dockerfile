FROM python:3-alpine

LABEL Description="Web Monitor"

RUN \
 apk add --no-cache curl unzip \
 && python3 -m venv /opt/python3-ven \
 && curl -sSL https://api.github.com/repos/drwetter/testssl.sh/releases/latest \
   | grep browser_download_url \
   | grep 'testssl.sh-.*.zip' \
   | cut -d '"' -f 4 \
   | xargs curl -L -o /tmp/testssl.zip \
 && unzip /tmp/testssl.zip -d /opt/ \
 && mv /opt/testssl.sh-* /opt/testssl.sh \
 && chmod +x /opt/testssl.sh/testssl.sh \
 && rm /tmp/testssl.zip

COPY requirements.txt /
RUN /opt/python3-ven/bin/pip3 install -r requirements.txt

COPY *.py /

CMD ["/opt/python3-ven/bin/python3", "/web-monitor.py", "/config/web-monitor.cfg"]
