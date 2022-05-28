# HappyTaps
Happy hour integration for Slack

This simple backend for a slash command will lookup the top 20 bars near the location provided (defaults to 'NYC') and randomly pick one to print information about.  Users in the slack group can then vote with emojis on whether or not to go to that establishment.  No more arguing about where to go after punching your time card!

Usage:
/happytaps [Location]

For example:
/happytaps greenpoint

Would yield something like this:

![screenshot](https://github.com/irishroryc/HappyTaps/blob/master/happytaps_screenshot.png?raw=true)

## Technical details

This code is deployed as two containerized apps on GCP Cloud Run.

The frontend serves requests from Slack, it basically just sends an ack back and then publishes information to pubsub for subsequent processing.

The findtaps service has a push subscription enabled from pubsub, once it receives a message it will lookup bars in the area and return information for one of them to the Slack channel where the request was initiated.

Below is a network architecture diagram detailing how this all works together.  Enjoy!

![network diagram](https://github.com/irishroryc/HappyTaps/blob/master/happytaps_architecture.png?raw=true)

## Observability

In order to get a better sense of where time is spent within the happytaps-findtaps service I have added Open Telemetry instrumentation to the code.

This provides visibility into time spent on external API calls to Yelp Fusion, as well as time spent updating cached business information in datastore.

![image](https://user-images.githubusercontent.com/20443817/170841740-f89c3a71-2040-4fb9-adde-3d5d89c62e84.png)

This could prove useful when looking to optimize performance in the future.

## Try it out!

Feel free to install the application yourself and give it a shot in your Slack workspace!

[![Add to Slack](https://platform.slack-edge.com/img/add_to_slack.png)](https://slack.com/oauth/v2/authorize?state=0cef27aa-a680-4ea6-bc55-2fe986277606&client_id=879979531745.945744536726&scope=commands,incoming-webhook&user_scope=)
