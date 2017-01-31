#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This script uses the Twitter streaming API to wait for tweets by Donald Trump,
then causes them to be archived at the Internet Archive, hopefully before The
Donald deletes them.

First steps here were based partly on http://stackoverflow.com/a/38192468/5562328
-- thanks kmario23.
"""


import time, json, requests

from social_media_auth import Trump_client                      # Unshared module that contains my authentication constants

#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from http.client import IncompleteRead


debugging = True

consumer_key = Trump_client['consumer_key']
consumer_secret = Trump_client['consumer_secret']
access_token = Trump_client['access_token']
access_token_secret = Trump_client['access_token_secret']

Trump_twitter_accounts = ['25073877', '822215679726100480']     # @realDonaldTrump = 25073877; @POTUS = 822215679726100480
# Trump_twitter_accounts = ['814046047546679296']               # @false_trump = 814046047546679296


def get_tweet_url(username, id):
    return "https://twitter.com/%s/status/%s" % (username, id)

class TrumpListener(StreamListener):
    """Donald Trump is an abusive, sexist, racist, jingoistic pseudo-fascist. It's
    best to avoid actually paying attention to what he writes. Let's create a
    bot to listen for us. 
    """

    def __init__(self):
        StreamListener.__init__(self)

    def on_data(self, data):
        data = json.loads(data)
        if data['user']['id_str'] in Trump_twitter_accounts:
            if debugging: print("New tweet from %s: %s" % (data['text'], data['user']['screen_name']))
        return True

    def on_error(self, status):
        print(status)


if __name__ == '__main__':
    if debugging: print('Starting up...')
    l = TrumpListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    if debugging: print("... OK, we're set up")

    while True:
        try:
            stream = Stream(auth, l)
            stream.filter(follow=Trump_twitter_accounts, stall_warnings=True)
        except IncompleteRead as e:
            # Oh well. Sleep some before trying again
            time.sleep(15)
            continue
        except KeyboardInterrupt:
            stream.disconnect()
            break