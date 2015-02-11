FROM ubuntu:trusty
MAINTAINER Mattias Appelgren, mattias@ppelgren.se

WORKDIR /tmp

ADD build /tmp/

#RUN apt-get update \
#    && apt-get --yes --quiet upgrade \
#    && apt-get --yes --quiet install build-essential \
#    pandoc \
#    texlive \
#    texlive-latex-extra \
#    texlive-bibtex-extra \
#    biber \
#    python \
#    python-pygments \
#    zip

RUN apt-get update && apt-get --yes --quiet install zip
