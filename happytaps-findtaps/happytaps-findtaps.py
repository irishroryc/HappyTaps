import os
from slack_bolt import App
import requests
import random
import json

YELP_URL = "https://api.yelp.com/v3/businesses/search"

yelp_api_key = os.environ.get("YELP_API_KEY")
yelp_headers = {'Authorization':'Bearer '+yelp_api_key}
yelp_limit = 20

app = App(
	token=os.environ.get("SLACK_BOT_TOKEN"),
	signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# The echo command simply echoes on command
@app.command("/happytaps")
def happy_taps(ack, body, respond):
    ack("One watering hole coming up!")
    if 'text' in body:
        yelp_location = body['text']
    else:
        yelp_location = 'NYC'
    find_taps(respond, yelp_location)
    return


def find_taps(respond, yelp_location):
    yelp_params = {'location':yelp_location,'term':'bar','limit':yelp_limit,'price':'1,2,3',}
    r = requests.get(url = YELP_URL, headers=yelp_headers, params=yelp_params)
    yelp_data = r.json()
    
    print("data=",json.dumps(yelp_data))
    
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

    num_businesses = len(yelp_data['businesses'])

    random_choice = random.randint(0,num_businesses)
    bar = yelp_data['businesses'][random_choice]
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


    
# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
