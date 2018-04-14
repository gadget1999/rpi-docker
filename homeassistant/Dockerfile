FROM gadget1999/rpi-python3:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Home Assistant container for Raspberry Pi"

RUN apk add --update --no-cache mosquitto-clients && \
    pip3 install --no-cache-dir --upgrade setuptools pip && \
    pip3 install --no-cache-dir homeassistant && \
    pip3 install --no-cache-dir home-assistant-frontend && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

# Home Assistant port
EXPOSE 8123

CMD ["sh"]
