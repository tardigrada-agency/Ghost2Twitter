import logging
import os

from starlette.responses import RedirectResponse
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import tweepy
import yaml

# Setup logging
logger = logging.getLogger('Ghost2Twitter')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
    datefmt='[%Y-%m-%d %H:%M:%S %z]')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Setup FastAPI app
app = FastAPI()


class Config:
    consumer_key: str = ''
    consumer_secret: str = ''
    default_session: str = ''
    sessions: dict = {}
    rules: list = []
    path: str = 'config.yaml'

    def __init__(self, path: str = 'config.yaml'):
        """
        Init and read config
        :param path: path to config file
        """
        with open(path, 'r') as f:
            cfg = yaml.safe_load(f)
        keys_to_check = ['default_session', 'sessions', 'consumer_key', 'consumer_secret']
        for key in keys_to_check:
            if key not in cfg.keys():
                logger.error(f'{key} not in config, you must set it!')
                exit(1)
        if cfg['default_session'] not in cfg['sessions'].keys():
            logger.error('default_session not in config.sessions, you must set it!')
            exit(1)
        self.consumer_key = cfg['consumer_key']
        self.consumer_secret = cfg['consumer_secret']
        self.default_session = cfg['default_session']
        self.sessions = cfg['sessions']
        self.path = path
        if 'rules' in cfg.keys():
            self.rules = cfg['rules']
            self.__test_rules()
        self.__test_sessions()

    def safe_config(self):
        """
        Save config to .yaml file
        :return:
        """
        cfg = {
            'consumer_key': self.consumer_key,
            'consumer_secret': self.consumer_secret,
            'default_session': self.default_session,
            'sessions': self.sessions
        }
        if self.rules != {}:
            cfg['rules'] = self.rules
        with open(self.path, 'w') as f:
            yaml.dump(cfg, f)
        logger.info('Config saved')

    def __test_sessions(self):
        for session_name, session in self.sessions.items():
            try:
                auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
                auth.set_access_token(session['access_token'], session['access_token_secret'])
                api = tweepy.API(auth)
                api.get_settings()
            except tweepy.errors.TweepyException:
                logger.error(f'Test of consumer_key, consumer_secret and default_session failed for {session_name}, '
                             'please recheck them and try again.')
                exit(1)

    def __test_rules(self):
        for rule in self.rules:
            if rule['session'] not in self.sessions.keys():
                logger.error(f'Test of rules failed for rule with session {rule["session"]}, '
                             'cannot find session in sessions')
                exit(1)

config = Config('config.yaml')


def new_tweet(text: str, session_name: str = config.default_session) -> None:
    """
    Tweet text to account
    :param text: Text to tweet
    :param session_name: Name of account, where publish tweet
    :return:
    """
    session = config.sessions[session_name]
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(session['access_token'], session['access_token_secret'])
    api = tweepy.API(auth)
    api.update_status(text)
    logger.info(f'{session_name}: {text}')


@app.get('/')
async def root():
    """
    Redirect user to twitter login url
    :return:
    """
    # Creating twitter auth link
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret,
                               'http://127.0.0.1:8084/twitter-login')
    redirect_url = auth.get_authorization_url()
    # Redirect user to twitter login
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get('/twitter-login')
async def twitter_login(oauth_token: str = '', oauth_verifier: str = '') -> JSONResponse:
    """
    Handle redirect from twitter login url and save session
    :param oauth_token: Twitter oauth_token for account
    :param oauth_verifier: Twitter oauth_verifier for account
    :return:
    """
    # Preparation
    response = {'status': 'success', 'msg': ''}
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.request_token = {'oauth_token': oauth_token,
                          'oauth_token_secret': oauth_verifier}

    #  Trying to get token
    try:
        auth.get_access_token(oauth_verifier)
    except tweepy.errors.TweepyException:
        logging.error(f'Failed to get access token.')
        response = {'status': 'error', 'msg': 'Failed to get access token.'}
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)

    # Getting username of account
    api = tweepy.API(auth)
    screen_name = api.get_settings()['screen_name']
    logger.info(f'{screen_name} added to config.sessions')

    # Saving session
    config.sessions[screen_name] = {
        'access_token': auth.access_token,
        'access_token_secret': auth.access_token_secret
    }
    config.safe_config()

    # Responding
    if response['status'] == 'success':
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
    else:
        logger.error('twitter-login: ' + response['msg'])
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)


@app.post('/new_post')
async def new_post(post: Request) -> JSONResponse:
    """
    Handle webhook from Ghost, when post published
    :param post: Post json from Ghost
    :return:
    """
    # Preparation
    logger.info(f'New post from Ghost!')
    response = {'status': 'success', 'msg': ''}
    tweet = ''
    session_name = config.default_session
    post = await post.json()
    post = post['post']

    # Creating tweet
    if post['current']['twitter_title']:
        tweet += post['current']['twitter_title']
    else:
        tweet += post['current']['title']
    tweet += '\n\n'
    tweet += post['current']['url']

    # Some checks
    if len(tweet) > 280:
        response['status'] = 'error'
        response['msg'] = 'Tweet can\'t be more than 280 characters'
    if config.default_session not in config.sessions.keys():
        response['status'] = 'error'
        response['msg'] = 'Wrong default_session in the config.yaml'

    # Processing rules
    for rule in config['rules']:
        if rule['type'] == 'primary-tag':
            if not post['current']['primary_tag']:
                continue
            if rule['tag'] == post['current']['primary_tag']['slug']:
                logger.info(f'post.primary_tag is {rule["tag"]}): {rule["session"]}')
                session_name = rule['session']

    # Tweeting
    new_tweet(tweet, session_name)

    # Responding
    if response['status'] == 'success':
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
    else:
        logger.error('new-post: ' + response['msg'])
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)


if __name__ == '__main__':
    # if started via python
    os.system('uvicorn main:app --host 0.0.0.0 --port 8084')
