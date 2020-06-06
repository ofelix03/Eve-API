FROM python:3.6-buster

RUN mkdir -p /usr/src/api/api/.
WORKDIR /usr/src/api/api/.
COPY api/ .
RUN pip install -r ./requirements.txt
ENV PYTHONPATH /usr/src/api

RUN apt-get update --fix-missing
RUN apt-get install -y curl
RUN apt-get install -y build-essential libssl-dev software-properties-common

RUN apt-get install wget curl
RUN curl -sL https://deb.nodesource.com/setup_11.x |  bash -

RUN  apt-get install -y nodejs

RUN npm install pm2@latest -g

RUN apt-get install -y nginx
COPY nginx/ /etc/nginx/

RUN apt-get install -y vim

COPY ./gunicorn_start.sh .
COPY ./nginx_start.sh .


EXPOSE 8000
EXPOSE 8050


COPY ./startup.sh .
RUN chmod +x ./startup.sh

CMD  ./startup.sh
