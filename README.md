# Ghost2Twitter

```
MAKE SURE YOUR Ghost2Twitter INSTANCE IS NOT AVAILABLE FROM INTERNET
```
Ghost2Twitter - microservice built to simplify posting from Ghost.org to Twitter. It stands out for being completely selfhosted and allowing you to create rules to post to different accounts.
## Preparation and configuration

0. You need to create a Twitter developer account and an application in it, read about it on the Internet.
1. Go to [Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Select your App
3. Click edit near OAuth and add http://127.0.0.1:8084/twitter-login to Callback URI / Redirect URL, select Read and write in App permissions
4. Go back to your app page and click Keys and tokens
5. Open config.yaml in a editor like nano or vim
6. Copy consumer_key and consumer_secret from Consumer Keys to config, quotes are not required
7. Replace ACCOUNT_NAME in sessions and default_session with your twitter developer account username like tardigrada_ag
8. Copy Access Token and Secret and paste them into sessions/ACCOUNT_NAME/access_token и access_token_secret

## Running in Docker
Launching in Docker is the recommended option, it is the easiest and fastest.

0. Install docker and docker-compose
1. cd to directory where you clone this project
2. Run docker-compose up -d --build
3. If your Ghost run's in Docker, than add Ghost2Twitter and Ghost to same docker network, read about it [here](https://docs.docker.com/network/) and [here](https://docs.docker.com/compose/networking/)

note: Ghost does not allow domains without a dot in webhooks, so you have to add a dot in the container name, for example .local at the end.

## Running without Docker

This method is not recommended, it is less convenient and longer.

0. Install python3 and pip (`# apt install python3 python3-pip` for debian and ubuntu)
1. cd to directory where you clone this project
2. Install requirements `python3 -m pip install -r requirements.txt`
3. and finnaly run `uvicorn main:app --host 127.0.0.1 --port 8084`

## Setup Accounts and Rules 

Now you can go to http://127.0.0.1:8084/ for each of your accounts and login via twitter. For rules add "rules:" to your config,yaml and start new rule with "-". 
Each rule has 3 variables:
1. session - username of the Twitter account, it must be in sessions
2. type - rule type while only one is supported (primary-tag)
3. text to check, for the primary-tag slug of tag from Ghost

## Connect with Ghost

To work with Ghost, we need to set up an integration and a webhook, without it nothing will work.

1. Go to https://YOUR_GHOST/ghost/#/settings/integrations and click green button with text "Add custom integration" on it
2. Choose a name such as Ghost2Twitter, it can be anything and click "Create"
3. Now you can upload logo.png as icon and enter Description, but this is optional
4. Click "Add webhook"
5. Enter Name (example "New post published")
6. Select Event "Post published"
7. Enter Target URL, http://ghost2twitter.local:8084/new_post for docker and http://127.0.0.1:8084/new_post for without docker installation.
8. Click "Create"


Now everything should work, the project has been created for the Tardigrad, but you can use it observing the license.
If you need any help, you can contact the developers at mail [a@slnk.icu](mailto:a@slnk.icu) or telegram [@luck20yan](https://t.me/luck20yan)
