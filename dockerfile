FROM python:3.7-slim-buster

ARG BOT_TOKEN=${BOT_TOKEN:-""}
ENV BOT_TOKEN=${BOT_TOKEN}

WORKDIR /app
ADD requirements.txt requirements.txt
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

RUN pip install pip==20.0.2
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY ./ ./

EXPOSE 5000
CMD ["gunicorn", "-b", ":5000", "app:app"]
