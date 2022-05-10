import os
from slack_bolt.context.respond.respond import Respond
import requests
import random
import json
from google.cloud import datastore, pubsub_v1
from datetime import datetime, timedelta, timezone
from flask import Flask, request

app = Flask(__name__)


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
    attributes = request.form['attributes']
    print("Attributes type - ",type(attributes))
    for i in attributes.key():
        print("key = ",i)

    # Respond object used to send results back to Slack
    respond = Respond(response_url=attributes['response_url'])
    yelp_location = attributes['yelp_location']

    # Attempt to get data from datastore for this location
    data_key = datastore_client.key("HappyTaps",yelp_location)
    data_response = datastore_client.get(data_key)

    # If data is up to date in datastore, use this for response
    if data_response is not None and (data_response['timestamp'] > datetime.now(tz=timezone.utc) + timedelta(weeks = -2)):
        yelp_businesses = data_response['businesses']

    # Otherwise we need to pull new business list from Yelp
    else:
        # Format and make request to Yelp API
        yelp_params = {'location':yelp_location,'term':'bar','limit':YELP_LIMIT,'price':'1,2,3',}
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
            return
        # If there are businesses, update in datastore and use for reponse
        else:
            update_taps(yelp_location, yelp_data['businesses'])
            yelp_businesses = yelp_data['businesses']
    
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
    app.run(port=int(os.environ.get("PORT", 3000)))
