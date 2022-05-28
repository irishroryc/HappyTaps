import os
import logging
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_oauth_datastore import GoogleDatastoreInstallationStore, GoogleDatastoreOAuthStateStore
from google.cloud.datastore import Client
from google.cloud import pubsub_v1

# Initialize datastore client
datastore_client: Client = Client()

# Define logger and set log level
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create GoogleInstallationStore for use with Slack OAuth settings
my_install_store = GoogleDatastoreInstallationStore(
        datastore_client=datastore_client,
        datastore_bot_kind = "HappyTaps-Bot",
        datastore_installation_kind = "HappyTaps-Installation",
        client_id=os.environ["SLACK_CLIENT_ID"],
        logger=logger,
    )

# Create GoogleDAtaStoreOAuthStateStore for use with Slack OAuth settings
my_state_store = GoogleDatastoreOAuthStateStore(
        datastore_client=datastore_client,
        datastore_state_kind="HappyTaps-OAuthStateStore",
        expiration_seconds=600,
        logger=logger,
    )

# Define OAuthSettings for HappyTaps app using install and state store
oauth_settings = OAuthSettings(
    client_id=os.environ["SLACK_CLIENT_ID"],
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    scopes=["commands", "incoming-webhook"],
    installation_store=my_install_store,
    state_store=my_state_store
)


# Initialize the slack app
app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    oauth_settings=oauth_settings
)

# Initialize pubsub
publisher = pubsub_v1.PublisherClient()
pubsub_topic = 'projects/clear-router-191420/topics/find-taps'

# HappyTaps command entrypoint
@app.command("/happytaps")
def happy_taps(ack, body, respond):
    # Reply with messaging to user right away
    ack("One watering hole coming up!")

    # Check if a specific location was specified, if not default to NYC
    if 'text' in body:
        yelp_location = body['text']
    else:
        yelp_location = 'NYC'

    # Store the response url for channel where HappyTaps request originated
    response_url = str(respond.response_url)

    # Publish details of HappyTaps request to the FindTaps pubsub topic
    future = publisher.publish(pubsub_topic,b'FindTaps',location=yelp_location,response_url=response_url)

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
