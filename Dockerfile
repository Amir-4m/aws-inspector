FROM python:3.8

# set work directory
WORKDIR /src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy project
COPY . /src/

# install dependencies
RUN apt-get update && apt-get install curl vim cron -y
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN chmod 0755 main.py && chmod 0644 aws_cron && mv aws_cron /etc/cron.d/
RUN crontab /etc/cron.d/aws_cron && touch /var/log/cron.log

# run cron
CMD cron && tail -f /var/log/cron.log
