FROM python:3.9-alpine

RUN adduser -D happytaps
USER happytaps

WORKDIR /home/happytaps

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt

COPY happytaps-frontend.py happytaps-frontend.py
COPY boot.sh boot.sh

EXPOSE 3000
ENTRYPOINT ["./boot.sh"]
