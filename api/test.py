import threading
import os
from flask import abort, Flask, jsonify, request
import requests
import random

# App Engine looks for an an app called 'app' in main.py
# Can override with 'entrypoint' in app.yaml if desired
app = Flask(__name__)

# Defining constants to be used in app
YELP_LIMIT = 20
YELP_URL = "https://api.yelp.com/v3/businesses/search"
YELP_API_KEY = "s9ubWgZUY8dY0JgMaAKe7W_YeKLhKfHh7Rzp4_vW6wos3TfGPJ308X_xIYdz4ecnZwUOIyWCXSerpd3-QmRJP9GPNgSKGNgayZc-3rZu8NkHW_25bv8vKEwdXx3cXHYx"
YELP_HEADERS = {'Authorization':'Bearer '+YELP_API_KEY}

def is_request_valid(request):
    is_token_valid = True 
    print("token =",request.form['token'])
    is_team_id_valid = True
    print("team =",request.form['team_id'])

    return is_token_valid and is_team_id_valid

@app.route('/zendesk_oauth', methods=['POST'])
def zendesk_print():
    print("DEBUG: request.url = ",request.url)
    print("DEBUG: request.data = ",request.data)
    print("DEBUG: request.args = ",request.args)
    print("DEBUG: request.form = ",request.form)
    print("DEBUG: request.endpoint = ",request.endpoint)
    print("DEBUG: request.method = ",request.method)
    print("DEBUG: request.data =",request.data)
    return ''

@app.route('/slack-interactive', methods=['POST'])
def print_payload():
    print("DEBUG: request.url = ",request.url)
    print("DEBUG: request.data = ",request.data)
    print("DEBUG: request.args = ",request.args)
    print("DEBUG: request.form = ",request.form)
    print("DEBUG: request.endpoint = ",request.endpoint)
    print("DEBUG: request.method = ",request.method)
    print("DEBUG: request.data =",request.data)
    return ''

@app.route('/happytaps', methods=['POST'])
def happy_taps():
    if not is_request_valid(request):
        abort(400)

    req_location = 'NYC'
    if request.form['text']:
        req_location = request.form['text']

    req_url = request.form.get('response_url')

    yelp_thread = threading.Thread(
        target = find_taps,
        args=(req_url,req_location)
    )
    yelp_thread.start()

    return "One watering hole coming right up!"

def find_taps(response_url, yelp_location):
    YELP_PARAMS = {'location':yelp_location,'term':'bar','limit':YELP_LIMIT,'price':'1,2,3',}
    r = requests.get(url = YELP_URL, headers=YELP_HEADERS, params=YELP_PARAMS)
    data = r.json()

    # TODO:
    # Need to handle bad status codes from Yelp - example: LOCATION_NOT_FOUND
    # 400 error

    random_limit = YELP_LIMIT
    if len(data['businesses']) < YELP_LIMIT:
        random_limit = len(data['businesses'])

    random_choice = random.randint(0,random_limit)

    bar = data['businesses'][random_choice]
    bar_name = bar['name']
    bar_url = bar['url']
    bar_pic = bar['image_url']
    bar_pretext = "Let's drink some dranks near "+yelp_location+", what do you think about this?"

    tap_data = {
        'response_type':'in_channel',
        'text':"HAPPY HOURRRRRR!!!!!!",
        'attachments':[{'pretext':bar_pretext,'image_url':bar_pic,'title':bar_name,'title_link':bar_url}]
    }

    result = requests.post(response_url,json=tap_data)
    print("DEBUG: result = :",result.status_code)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
