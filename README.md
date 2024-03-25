# Services-Status

The Services-Status repository is used to power the status page used by network engineers at CIARA (https://status.amlight.net/) It uses Django + jQuery to run the web server, supplying templates based on what view you are currently in.

For documentation, on tech used and useful tips, check DEV_TIPS.md

## Recent Changes

### Testing

- For quicker development and testing, the logging driver was commented out from docker-compose.yml. When pushing to production remember to uncomment this.

## Deployment Methodology

The Service Status application uses Docker to gather its dependencies and deploy onto a remote server. It uses a .yml script to build, so this application uses docker-compose.

To **test**, make sure to turn Debug = True and SESSION_COOKIE_COOKIE = False. You can find more information on how to do this in the DEV_TIPS.md file.

## Unix (remote environment)

The services-status application was created to run on a Unix environment, which is the environment used by the remote server. Currently, development is taking place on a virtual machine, so ask the networking team to help you gain access to the current VM the developers are using, or to create your own. 
