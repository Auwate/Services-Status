# Services-Status

The Services-Status repository is used to power the status page used by network engineers at CIARA (https://status.amlight.net/) It uses Django + jQuery to run the web server, supplying templates based on what view you are currently in.

For documentation, on tech used and useful tips, check DEV_TIPS.md

## Recent Changes

- Tickets are now ordered in descending order by the *begin* field (Newest first)
- Tickets in the main view now contain a latest_update field, which uses the action_description found in TicketLogs.
- Custom command added to immediately populate the database with Status objects, if they are not there already.
- Unit tests are being rolled out to test new features.
- Documentation is being rolled out on a daily basis.

## Unit Testing

Testing is implemented by running the following command:
```
python3 manage.py test status.tests --settings=ServiceStatus.settings-test
```
(If python3 does not work, use **python**)

### Development

To create more tests, navigate to the status/tests directory. Each test will be run since they start with *test_*, so write your tests under the test file that covers your domain. For example, if you're testing a new command, do it under *test_commands*.

## Logging Driver

For quicker development and testing, the logging driver was commented out from docker-compose.yml. When pushing to production remember to uncomment this.

## Deployment Methodology

The Service Status application uses Docker to gather its dependencies and deploy onto a remote server. It uses a .yml script to build, so this application uses docker-compose.

To **test**, make sure to turn Debug = True and SESSION_COOKIE_COOKIE = False. You can find more information on how to do this in the DEV_TIPS.md file.

## Unix (remote environment)

The services-status application was created to run on a Unix environment, which is the environment used by the remote server. Currently, development is taking place on a virtual machine, so ask the networking team to help you gain access to the current VM the developers are using, or to create your own. 
