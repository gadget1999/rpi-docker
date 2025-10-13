# syntax=docker/dockerfile:1.7
FROM debian:trixie-slim

LABEL maintainer="gadget1999 <gadget1999@outlook.com>"
LABEL Description="CUPS with driver for Canon D420, to turn it into a network printer."

ENV DEBIAN_FRONTEND=noninteractive

# Let Buildx set architecture automatically
ARG TARGETARCH

# Install CUPS and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cups cups-client cups-bsd avahi-daemon avahi-utils wget gnupg ca-certificates sudo && \
    rm -rf /var/lib/apt/lists/*

# Copy the Canon UFRII driver package for the right architecture (optional)
# Place these files in your build context as:
#   cnrdrvcups-ufr2-us_6.20-1.01_amd64.deb
#   cnrdrvcups-ufr2-us_6.20-1.01_arm64.deb
COPY cnrdrvcups-ufr2-us_6.20-1.01_${TARGETARCH}.deb /tmp/canon.deb

# Install the driver if the .deb file is present
RUN set -eux; \
    if [ -f /tmp/canon.deb ]; then \
        echo "Installing Canon UFRII driver for ${TARGETARCH}..."; \
        apt-get update && apt-get install -y ./tmp/canon.deb || true; \
    else \
        echo "⚠️ No Canon driver provided for ${TARGETARCH}, skipping..."; \
    fi; \
    # Clean up apt cache and .deb files
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/*.deb /var/tmp/*

# --- Configure CUPS ---
RUN sed -i 's|Listen localhost:631|Port 631|' /etc/cups/cupsd.conf && \
    sed -i 's|<Location /admin>|<Location /admin>\n  Allow all|' /etc/cups/cupsd.conf && \
    sed -i 's|<Location />|<Location />\n  Allow all|' /etc/cups/cupsd.conf && \
    cupsenable || true && cupsaccept || true

# Add a test user for web access
RUN useradd -m printer && echo "printer:printer" | chpasswd && adduser printer lpadmin

EXPOSE 631
VOLUME ["/etc/cups", "/var/log/cups", "/var/spool/cups"]

CMD ["/usr/sbin/cupsd", "-f"]
