import threading
import os
from flask import abort, Flask, jsonify, request
import requests
import random
from google.cloud import secretmanager_v1
import googlecloudprofiler
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
import opencensus.trace.tracer



try:
  import googleclouddebugger
  googleclouddebugger.enable()
except ImportError:
  pass

try:
    googlecloudprofiler.start(service="service_api",verbose=3)
except (ValueError, NotImplementedError) as exc:
    print(exc) # Handle errors here

# App Engine looks for an an app called 'app' in main.py
# Can override with 'entrypoint' in app.yaml if desired
app = Flask(__name__)

# Defining constants to be used in app
YELP_LIMIT = 20
YELP_URL = "https://api.yelp.com/v3/businesses/search"
#YELP_API_KEY = os.environ['YELP_API_KEY'] 
#YELP_HEADERS = {'Authorization':'Bearer '+YELP_API_KEY}

# Using Google secrets manager to populate YELP_API_KEY
secret_client = secretmanager_v1.SecretManagerServiceClient()
secret_path = secret_client.secret_version_path('clear-router-191420','YELP_API_KEY',1)
YELP_API_KEY = secret_client.access_secret_version(secret_path).payload.data.decode("utf-8")
YELP_HEADERS = {'Authorization':'Bearer '+YELP_API_KEY}


def initialize_tracer():
    print("DEBUG: Running initialize_tracer()")
    exporter =
    stackdriver_exporter.StackdriverExporter()
    tracer = opencensus.trace.tracer.Tracer(
        exporter=exporter,
        sampler=opencensus.trace.tracer.samplers.AlwaysOnSampler()
    )
    return tracer

def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    print("token_valid = ",is_token_valid)
    print("team_valid = ",is_team_id_valid)

    return is_token_valid and is_team_id_valid

@app.route('/interactive-endpoint', methods=['POST'])
def print_payload():
    print(request.url, request.headers, request.body)

@app.route('/happytaps', methods=['POST'])
def happy_taps():
    tracer = app.config['TRACER']
    tracer.start_span(name='happytaps')
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

    tracer.end_span()
    return "One watering hole coming right up!"

def find_taps(response_url, yelp_location):
    tracer = app.config['TRACER']
    tracer.start_span(name='find_taps')
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
    tracer.end_span()

if __name__ == '__main__':
    # Define tracer without a project, this will be picked up automatically in GCP
    tracer = initialize_tracer()
    app.config['TRACER'] = tracer
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
