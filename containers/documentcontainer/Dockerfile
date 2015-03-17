FROM ubuntu:trusty
MAINTAINER Mattias Appelgren, mattias@ppelgren.se

WORKDIR /tmp

RUN apt-get update \
    && apt-get --yes --quiet upgrade \
    && apt-get --yes --quiet install build-essential \
    pandoc \
    texlive \
    texlive-latex-extra \
    texlive-bibtex-extra \
    biber \
    python \
    python-pygments \
    zip

RUN useradd runner

USER runner

ADD build /tmp/
