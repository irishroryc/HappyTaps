#!/bin/bash
docker build -t happytaps-frontend .
docker tag happytaps-frontend us-central1-docker.pkg.dev/clear-router-191420/happytaps-frontend/happytaps-frontend:latest
docker push us-central1-docker.pkg.dev/clear-router-191420/happytaps-frontend/happytaps-frontend:latest
