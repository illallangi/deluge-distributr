FROM ghcr.io/illallangi/toolbx:v0.0.13 as toolbx

FROM docker.io/library/python:3.12.0

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    XDG_CONFIG_HOME=/config

# install gosu
COPY --from=toolbx /usr/local/bin/gosu /usr/local/bin/gosu

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN \
  python3 -m pip install --no-cache-dir \
    .

#set entrypoint
ENTRYPOINT ["./custom-entrypoint"]

# set command
CMD ["/usr/local/bin/deluge-distributr"]
