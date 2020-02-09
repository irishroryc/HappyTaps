from flask import Flask, request

# App Engine looks for an an app called 'app' in main.py
# Can override with 'entrypoint' in app.yaml if desired
app = Flask(__name__)

@app.route('/web/index')
def welcome():
    return "Welcome from the WEB!"
