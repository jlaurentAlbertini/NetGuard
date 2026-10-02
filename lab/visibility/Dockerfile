FROM alpine:3.23.6@sha256:85fe1e81d6758c208f3e1eed4338a1997e19d4be002d4dd32d3100c9a8c010a0
WORKDIR /opt/lab
COPY packages.lock ./
RUN set -eu; set -f; \
    apk add --no-cache $(cat packages.lock); \
    awk '/^P:/{name=substr($0,3)} /^V:/{print name "=" substr($0,3)}' /lib/apk/db/installed \
      | LC_ALL=C sort > /tmp/installed.lock; \
    diff -u packages.lock /tmp/installed.lock; \
    rm /tmp/installed.lock
COPY roles.py checks.py ./
ARG LAB_SOURCE_SHA256=unverified
LABEL org.opencontainers.image.version="1.5" \
      org.netguard.lab.sources-sha256="${LAB_SOURCE_SHA256}"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/opt/lab/roles.py"]
