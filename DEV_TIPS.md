# Reading Markdown Files

To read Markdown files (.md) in VS Code, press Ctrl+Shift+V for Markdown preview.

# Required Prerequisites

- Python
- HTML/CSS
- Django
- Docker
- SQL
- Linux/Unix

# Django

Documentation can be found at https://docs.djangoproject.com/en/3.0/

## Testing

In case of errors, turn on debug in settings-dev.py or by using the following command:
```
sed -i "s/DEBUG = False/DEBUG = True/g" /opt/Services-Status/ServiceStatus/settings.py
```

## HTTPS to HTTP

Django uses HTTP in testing environments, so make sure to turn SESSION_COOKIE_SECURE to False. You can do that in settings-dev.py, or by using the following command:
```
sed -i "s/SESSION_COOKIE_SECURE = True/SESSION_COOKIE_SECURE = False/g" /opt/Services-Status/ServiceStatus/settings.py
```

# Unix/Linux Environment

The application is built for Unix/Linux development, so locally developing the application on other operating systems is **not** recommended. Ask a network engineer or your lead developer to help give you access to the remote server being used to test.

Unix/Linux documentation can be found at https://docs.kernel.org/, or by searching up common commands used.

# Docker

Documentation can be found at https://docs.docker.com/

This application uses docker-compose to build and run, so before using any commands you must be in the deploy folder.

## Common Docker commands
```
docker-compose build
```
This will run the build script, pulling the data from the 3 Docker files found in the folder.
```
docker-compose up
```
This will run the docker container in your terminal. 
```
docker-compose up -d
```
This will run the docker container in the background. This is especially useful if you want to debug or enter into the shell.
```
docker-compose kill
```
This will terminate the running container so you do not consume excess resources. This is especially important if you run **docker-compose up -d** or if you run docker-compose up and disconnect from the terminal.
```
docker exec -it <container_name> /bin/bash
```
This will connect you into the container's bash terminal.
