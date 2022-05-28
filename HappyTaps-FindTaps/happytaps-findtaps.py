import os
from slack_bolt.context.respond.respond import Respond
import requests
import random
import json
import logging
from google.cloud import datastore
from datetime import datetime, timedelta, timezone
from flask import Flask, request, abort

# Tracing
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import (
    CloudTraceFormatPropagator,
)

set_global_textmap(CloudTraceFormatPropagator())
    
tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(
    # BatchSpanProcessor buffers spans and sends them in batches in a
    # background thread. The default parameters are sensible, but can be
    # tweaked to optimize your performance
    BatchSpanProcessor(cloud_trace_exporter)
)
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Intitialize Flask app that exposes endpoint for pubsub FindTaps subscription
app = Flask(__name__)

# Instrument Flask app for open telemetry tracing
FlaskInstrumentor().instrument_app(app)

# Define logger and set log level
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define values to be used with Yelp Fusion API calls
YELP_URL = "https://api.yelp.com/v3/businesses/search"
YELP_LIMIT = 20
yelp_api_key = os.environ.get("YELP_API_KEY")
yelp_headers = {'Authorization':'Bearer '+yelp_api_key}

# Instantiates a Google datastore client
datastore_client = datastore.Client()

# Route decorator specifying path for API call
@app.route('/findtaps', methods=['POST'])
# Function to generate bar suggestion for Slack
def find_taps():
    # Save attributes from pubsub push subscription message
    data = request.json
    attributes = data['message']['attributes']

    # Create respond object and set yelp_location from pubsub message
    respond = Respond(response_url=attributes['response_url'])
    yelp_location = attributes['location'].lower()

    # Attempt to get data from datastore for this location
    data_key = datastore_client.key("HappyTaps",yelp_location)
    data_response = datastore_client.get(data_key)

    # If data is up to date in datastore, use this for response
    if data_response is not None and (data_response['timestamp'] > datetime.now(tz=timezone.utc) + timedelta(days = -1)):
        yelp_businesses = data_response['businesses']

    # Otherwise we need to pull new business list from Yelp
    else:
        # Format and make request to Yelp API
        yelp_params = {'location':yelp_location,'term':'bar','limit':YELP_LIMIT,'price':'1,2,3',}
        with tracer.start_span("yelp_api_call") as yelp_span:
            r = requests.get(url = YELP_URL, headers=yelp_headers, params=yelp_params)
        yelp_data = r.json()

        # Respond with error message if no businesses come back from Yelp
        if 'businesses' not in yelp_data:
            respond(
                {
                    "response_type": "in_channel",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "No Happy Hour!!!!",
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "No bars are available near *"+yelp_location+"*! LAME!"
                                }
                            ]
                        }
                        ]
                }
            )
            return 'Ok', 200
        # If there are businesses, update in datastore and use for reponse
        else:
            yelp_businesses = yelp_data['businesses']
            with tracer.start_span("update_taps") as update_taps_span:
                update_taps(yelp_location, yelp_data['businesses'])
                update_taps_span.set_attribute("num_businesses",len(yelp_data['businesses']))
            
    
    # Ensure we don't exceed size of array when getting random bar
    num_businesses = len(yelp_businesses)
    random_choice = random.randint(0,num_businesses-1)

    # Pull bar at random and send reponse to Slack
    bar = yelp_businesses[random_choice]
    bar_name = bar['name']
    bar_url = bar['url']
    bar_pic = bar['image_url']
    bar_pretext = "Let's get some drinks near *"+yelp_location+"*, what do you think about this?"
    respond(
        {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Happy Hour!!!!",
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": bar_pretext
                        }
                    ]
                },
                {
                    "type": "image",
                    "image_url": bar_pic,
                    "alt_text": "happy hour pic"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<"+bar_url+"|"+bar_name+">"
                    }
                }
            ]
        }
    )
    return 'Ok', 200


# Function to update business list in Cloud Datastore
def update_taps(yelp_location, updated_businesses):
    # Define key for datastore
    data_key = datastore_client.key("HappyTaps",yelp_location)

    # Define element to be updated in datastore
    # Must exclude 'businesses' from indexes as values are too long
    data_element = datastore.Entity(key=data_key, exclude_from_indexes=(['businesses']))
    data_element.update({
        "businesses":updated_businesses,
        "timestamp":datetime.now(tz=timezone.utc)
    })

    # Saves the entity to datastore
    datastore_client.put(data_element)

    

# Start your app
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3000)),debug=True)
