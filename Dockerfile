
FROM python:3-slim

ENV TZ=Etc/UTC
ENV LANG C.UTF-8

USER root
RUN groupadd -g 1000 mesh && useradd -ml -u 1000 -g 1000 mesh
RUN mkdir /app && chown mesh /app

USER mesh

WORKDIR /app

COPY requirements.txt /app
COPY mon.py /app
COPY plugin /app/plugin

RUN cd /app && pip3 install -r requirements.txt

CMD [ "python3", "/app/mon.py" ]

