FROM python:3.8-alpine

ENV FLASK_APP happytaps.py

RUN adduser -D happytaps
USER happytaps

WORKDIR /home/happytaps

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt

COPY happytaps.py happytaps.py
COPY boot.sh boot.sh
COPY .flaskenv .flaskenv

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
