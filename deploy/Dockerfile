FROM debian:buster

RUN apt update && apt-get upgrade -y

RUN  apt-get install -y python3-pip git nginx libmariadb-dev-compat

WORKDIR /opt

RUN git clone https://github.com/amlight/Services-Status.git

WORKDIR /opt/Services-Status

RUN pip3 install -r requirements.txt

RUN cp ServiceStatus/settings-dev.py ServiceStatus/settings.py

RUN mkdir static

RUN python3 manage.py collectstatic --no-input

COPY docker-startup.sh /
RUN chmod +x /docker-startup.sh
COPY nginx.conf /etc/nginx/sites-available/default

EXPOSE 80

CMD ["/docker-startup.sh"]
