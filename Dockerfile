FROM python:3.8

# set work directory
WORKDIR /src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy project
COPY . /src/

# install dependencies
RUN apt-get update && apt-get install curl vim cron -y \
   && pip install --upgrade pip && pip install -r requirements.txt && chmod 0755 /src/main.py \
   && chmod 0644 /src/aws_cron && mv /src/aws_cron /etc/cron.d/ && crontab /etc/cron.d/aws_cron \
   && touch /var/log/cron.log

# run cron
CMD ["cron", "-f"]

