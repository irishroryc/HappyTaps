#!/bin/bash
docker build -t happytaps-findtaps .
docker tag happytaps-findtaps us-central1-docker.pkg.dev/clear-router-191420/happytaps-findtaps/happytaps-findtaps:latest
docker push us-central1-docker.pkg.dev/clear-router-191420/happytaps-findtaps/happytaps-findtaps:latest
