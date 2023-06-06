# Event Subscribtion

Automation Template for Subscribing a User that has pressed a button or scanned a nfc tag \
Refernce automationTemplateCurrentUser file to get a yaml that will always return the name of the user executing the automation

For publishing messages to user reference the automationMessagePublisher file \
There is the full setup i use at the moment \
Please make sure to include the mode: parallel and set max: to atleast the number of users in your home assistant instance \
For every user one event will be fired and if that number is to low, the user will not be notified

The whole integration does not persist data at the moment. \
I want to do that, but i havent found a way persist a json object in home assistant.
