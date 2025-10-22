FROM python:3.11.6-slim

SHELL ["/bin/bash", "-c"]

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y curl \
  && apt-get clean

ARG INTERNAL_CDN_ENDPOINT="https://pub-b98da9b927f2447592b50cc76c3a8331.r2.dev"
ARG ETCD_BINARY="etcd-v3.5.14-linux-amd64.tar.gz"

RUN curl -O "$INTERNAL_CDN_ENDPOINT/bin/$ETCD_BINARY" \
    && sha256sum -c - <<<"b0b34298f53f6830f08e7ddc57fc74dc45563216a66e94d9e6b0b9e0b0281b34 $ETCD_BINARY" \
    && tar -xvzf etcd-v3.5.14-linux-amd64.tar.gz --strip 1 etcd-v3.5.14-linux-amd64/etcdctl \
    && mkdir -p /opt/etcd \
    && mv etcdctl /opt/etcd/

ARG WD="/opt/wahda"

WORKDIR $WD

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

ENV PYTHONPATH $WD:$WD/proto
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
