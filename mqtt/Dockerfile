FROM gadget1999/rpi-alpine:latest

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="Mosquitto container for Raspberry Pi"

RUN apk add --update --no-cache mosquitto && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

# MQTT ports
EXPOSE 1883 8883

CMD ["sh"]
