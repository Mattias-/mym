FROM ubuntu:trusty
MAINTAINER Mattias Appelgren, mattias@ppelgren.se

WORKDIR /tmp

RUN apt-get update \
    && apt-get --yes --quiet install build-essential \
    zip

#RUN useradd runner

#USER runner

ADD build /tmp/
