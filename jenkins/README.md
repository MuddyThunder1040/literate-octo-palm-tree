# Jenkins Pipeline

This folder contains the Jenkins pipeline for building the FastAPI app as a Docker image and pushing it to Docker Hub.

## Jenkins setup

Create a Jenkins username/password credential for Docker Hub and set its ID to `dockerhub-credentials`, or pass a different ID through the `DOCKERHUB_CREDENTIALS_ID` build parameter.

Set `DOCKERHUB_REPO` to your Docker Hub repository name:

```text
dockerhub-username/repository-name
```

The pipeline publishes two tags:

```text
dockerhub-username/repository-name:<jenkins-build-number>
dockerhub-username/repository-name:latest
```

The Jenkins agent must have Docker available and permission to run `docker build`, `docker login`, and `docker push`.
