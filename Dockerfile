FROM docker.io/library/python:3.10.2

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

# install gosu
RUN \
  apt-get update \
  && \
  apt-get install -y \
    gosu \
  && \
  apt-get clean

WORKDIR /usr/src/app

ADD . /usr/src/app

RUN pip3 install .

#set entrypoint
ENTRYPOINT ["./custom-entrypoint"]

# set command
CMD ["/usr/local/bin/deluge-distributr"]

ARG VCS_REF
ARG VERSION
ARG BUILD_DATE
LABEL maintainer="Andrew Cole <andrew.cole@illallangi.com>" \
      org.label-schema.build-date=${BUILD_DATE} \
      org.label-schema.description="TODO: SET DESCRIPTION" \
      org.label-schema.name="DelugeDistributr" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.url="http://github.com/illallangi/DelugeDistributr" \
      org.label-schema.usage="https://github.com/illallangi/DelugeDistributr/blob/master/README.md" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/illallangi/DelugeDistributr" \
      org.label-schema.vendor="Illallangi Enterprises" \
      org.label-schema.version=$VERSION
