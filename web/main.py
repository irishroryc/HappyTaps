import os
import requests
from flask import Flask, request, abort

try:
  import googleclouddebugger
  googleclouddebugger.enable()
except ImportError:
  pass

# App Engine looks for an an app called 'app' in main.py
# Can override with 'entrypoint' in app.yaml if desired
app = Flask(__name__)

@app.route('/web/index')
def welcome():
    return "Welcome from the WEB!"

def is_request_valid(request):
    # To be completed with signature verification
    return True

@app.route('/web/oauth_callback')
def oauth_callback():
    if not is_request_valid(request):
        abort(400)
    print("DEBUG -- AUTH: Executing /web/oauth_callback")

    data ='<h1>Callback code</h1><hr><br>'
    args_dict = request.args
    for key in args_dict:
        data += key+": "+args_dict[key]+"<br>"

    HT_CLIENT_ID = os.environ['HT_CLIENT_ID']
    print("DEBUG -- AUTH: HT_CLIENT_ID = ",HT_CLIENT_ID)
    HT_CLIENT_SECRET = os.environ['HT_CLIENT_SECRET']
    AUTH_CODE = request.args['code']
    access_data = {
        "client_id":HT_CLIENT_ID,
        "client_secret":HT_CLIENT_SECRET,
        "code":AUTH_CODE,
        "redirect_uri":"https://www.happytaps.net/web/oauth_callback"
    }
    result = requests.post('https://slack.com/api/oauth.v2.access',data=access_data)
    result_data = result.json()
    print("DEBUG -- AUTH:\n",result.json())

    data += "<br>Return values from oauth.access:<br>"
    for key in result_data:
        data+= "--> "+key+": "+str(result_data[key])+"<br>"
    return data
