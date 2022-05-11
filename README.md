# HappyTaps
Happy hour integration for Slack

This simple backend for a slash command will lookup the top 20 bars near the location provided (defaults to 'NYC') and randomly pick one to print information about.  Users in the slack group can then vote with emojis on whether or not to go to that establishment.  No more arguing about where to go after punching your time card!

Usage:
/happytaps [Location]

## Technical details

This code is deployed as two containerized apps on GCP Cloud Run.

The frontend serves requests from Slack, it basically just sends an ack back and then publishes information to pubsub for subsequent processing.

The findtaps service has a push subscription enabled from pubsub, once it receives a message it will lookup bars in the area and return information for one of them to the Slack channel where the request was initiated.

Below is a network architecture diagram detailing how this all works together.  Enjoy!

![network diagram](https://github.com/irishroryc/HappyTaps/blob/master/happytaps_architecture.png?raw=true)
