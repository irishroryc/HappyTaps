import os
import logging
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_oauth_datastore import GoogleDatastoreInstallationStore, GoogleDatastoreOAuthStateStore
from google.cloud.datastore import Client
from google.cloud import pubsub_v1

datastore_client: Client = Client()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

my_install_store = GoogleDatastoreInstallationStore(
        datastore_client=datastore_client,
        datastore_bot_kind = "HappyTaps-Bot",
        datastore_installation_kind = "HappyTaps-Installation",
        client_id=os.environ["SLACK_CLIENT_ID"],
        logger=logger,
    )

my_state_store = GoogleDatastoreOAuthStateStore(
        datastore_client=datastore_client,
        datastore_state_kind="HappyTaps-OAuthStateStore",
        expiration_seconds=600,
        logger=logger,
    )

oauth_settings = OAuthSettings(
    client_id=os.environ["SLACK_CLIENT_ID"],
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    scopes=["commands", "incoming-webhook"],
    installation_store=my_install_store,
    state_store=my_state_store
)

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
    ack("One watering hole coming up!")
    if 'text' in body:
        yelp_location = body['text']
    else:
        yelp_location = 'NYC'

    response_url = str(respond.response_url)
    future = publisher.publish(pubsub_topic,b'FindTaps',location=yelp_location,response_url=response_url)

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
