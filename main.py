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
YELP_API_KEY = os.environ['YELP_API_KEY'] 
YELP_HEADERS = {'Authorization':'Bearer '+YELP_API_KEY}

def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    print("token_valid = ",is_token_valid)
    print("team_valid = ",is_team_id_valid)

    return is_token_valid and is_team_id_valid


@app.route('/happytaps', methods=['POST'])
def happy_taps():
    if not is_request_valid(request):
        abort(400)
    if request.form['text']:
        YELP_LOCATION = request.form['text']
    else:
        YELP_LOCATION = 'NYC'
    YELP_PARAMS = {'location':YELP_LOCATION,'term':'bar','limit':YELP_LIMIT,'price':'1,2,3',}
    r = requests.get(url = YELP_URL, headers=YELP_HEADERS, params=YELP_PARAMS)
    data = r.json()
    random_choice = random.randint(0,YELP_LIMIT)
    bar = data['businesses'][random_choice]
    bar_name = bar['name']
    bar_url = bar['url']
    bar_pic = bar['image_url']
    bar_pretext = "Let's drink some dranks near "+YELP_LOCATION+", what do you think about this?"
    return jsonify(
	response_type='in_channel',
	text="HAPPY HOURRRRRR!!!!!!",
	attachments=[{'pretext':bar_pretext,'image_url':bar_pic,'title':bar_name,'title_link':bar_url}]
    )

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
