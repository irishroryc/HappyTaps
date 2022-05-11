import os
from slack_bolt import App
from google.cloud import pubsub_v1


# Creates a Slack app instance
app = App(
	token=os.environ.get("SLACK_BOT_TOKEN"),
	signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
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
