# main image
FROM docker.io/library/python:3.12.1

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    XDG_CONFIG_HOME=/config

# install gosu
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && \
  apt-get install -y --no-install-recommends \
    gosu=1.14-1+b6 \
  && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN \
  python3 -m pip install --no-cache-dir \
    .

#set entrypoint
ENTRYPOINT ["./custom-entrypoint"]

# set command
CMD ["/usr/local/bin/deluge-distributr"]
