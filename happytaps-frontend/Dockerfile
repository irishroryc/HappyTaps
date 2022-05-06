FROM python:3.9-alpine

RUN adduser -D happytaps
USER happytaps

WORKDIR /home/happytaps

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt

ENV SLACK_BOT_TOKEN="xoxb-879979531745-943081499732-Z1BdjoxnTZTaHWre85sDq5UK"
ENV SLACK_SIGNING_SECRET="1e158889b82c8689751c217727470b15"
ENV YELP_API_KEY="s9ubWgZUY8dY0JgMaAKe7W_YeKLhKfHh7Rzp4_vW6wos3TfGPJ308X_xIYdz4ecnZwUOIyWCXSerpd3-QmRJP9GPNgSKGNgayZc-3rZu8NkHW_25bv8vKEwdXx3cXHYx"

COPY happytaps-frontend.py happytaps-frontend.py
COPY boot.sh boot.sh

EXPOSE 3000
ENTRYPOINT ["./boot.sh"]
