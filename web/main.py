from flask import Flask, request, abort

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


    data ='<h1>Callback code</h1><hr><br>'
    args_dict = request.args
    for key in args_dict:
        data += key+": "+args_dict[key]+"<br>"

    HT_CLIENT_ID = os.environ['HT_CLIENT_ID']
    HT_CLIENT_SECRET = os.environ['HT_CLIENT_SECRET']
    AUTH_CODE = request.args['code']
    access_data = {
        "client_id":HT_CLIENT_ID,
        "client_secret":HT_CLIENT_SECRET,
        "code":AUTH_CODE
    }
    result = requests.post('https://slack.com/api/oauth.access',json=access_data)
    print("DEBUG -- AUTH:\n",result.json)
    return data
