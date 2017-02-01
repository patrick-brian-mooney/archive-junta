#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This script uses the Twitter streaming API to wait for tweets by Donald Trump,
then causes them to be archived at the Internet Archive, hopefully before The
Donald deletes them.

First steps here were based partly on http://stackoverflow.com/a/38192468/5562328
-- thanks kmario23.
"""


import time, json, requests, sys

from tweepy.streaming import StreamListener                     # http://www.tweepy.org
from tweepy import OAuthHandler
from tweepy import Stream
from http.client import IncompleteRead

import pid                                                      # https://pypi.python.org/pypi/pid/


from social_media_auth import Trump_client                      # Unshared module that contains my authentication constants


consumer_key = Trump_client['consumer_key']
consumer_secret = Trump_client['consumer_secret']
access_token = Trump_client['access_token']
access_token_secret = Trump_client['access_token_secret']

Trump_twitter_accounts = ['25073877', '822215679726100480']     # [@realDonaldTrump, @POTUS] -- @false_trump = 814046047546679296
archiving_url_prefixes = ['http://web.archive.org/save/']

debugging = True




def get_tweet_urls(username, id):
    """Return all of the relevant URLs of the specified tweet. Currently, this
    just means that the http:// and https:// versions are returned
    """
    ret = "twitter.com/%s/status/%s" % (username, id)
    return "http://" + ret, "https://" + ret

class TrumpListener(StreamListener):
    """Donald Trump is an abusive, sexist, racist, jingoistic pseudo-fascist. It's
    best to avoid actually paying attention to what he writes. Let's create a
    bot to listen for us.
    """

    def on_data(self, data):
        data = json.loads(data)
        if data['user']['id_str'] in Trump_twitter_accounts:        # If it's one of the accounts we're watching, archive it.
            if debugging: print("New tweet from %s: %s" % (data['user']['screen_name'], data['text']))
            for which_url in get_tweet_urls(data['user']['screen_name'], data['id_str']):
                if debugging: print("archiving URL %s" % which_url)
                for which_prefix in archiving_url_prefixes:
                    if debugging: print("    ... archiving using prefix %s" % which_prefix)
                    req = requests.get(which_prefix + which_url)
                    for the_item in req.iter_content(chunk_size=100000): pass   # read the file to make the IArchive archive it.
        return True

    def on_error(self, status):
        print(status)

def startup():
    if debugging: print('Starting up...')
    


if __name__ == '__main__':
    try:
        with pid.PidFile(piddir='.'):
            startup()
            l = TrumpListener()
            auth = OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            if debugging: print("... OK, we're set up, and about to watch %s" % Trump_twitter_accounts)
        
            while True:
                try:
                    stream = Stream(auth, l)
                    stream.filter(follow=Trump_twitter_accounts, stall_warnings=True)
                except IncompleteRead as e:
                    # Sleep some before trying again.
                    time.sleep(15)
                    continue
                except KeyboardInterrupt:
                    stream.disconnect()
                    break
    except pid.PidFileError:
        if debugging: print("Already running! Quitting ...")
        sys.exit()