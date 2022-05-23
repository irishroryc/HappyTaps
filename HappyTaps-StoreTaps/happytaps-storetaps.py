import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request
from google.cloud import datastore

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# Instantiates a Google datastore client
datastore_client = datastore.Client()


@app.route('/storetaps', methods=['POST'])
# Function to update business list in Cloud Datastore
def store_taps():
    # Save attributes from pubsub push subscription message
    data = request.json
    attributes = data['message']['attributes']
    yelp_location = str(attributes['yelp_location'])
    updated_businesses = str(attributes['updated_businesses'])
    logging.info("yelp_location: "+yelp_location)
    logging.info("updated_businesses: "+updated_businesses)

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

    # Success return code to let pubsub know message delivered
    return 'Ok', 200

    

# Start your app
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3000)),debug=True)
