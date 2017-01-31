#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This script uses the Twitter streaming API to wait for tweets by Donald Trump,
then causes them to be archived at the Internet Archive, hopefully before The
Donald deletes them.

First steps here were based partly on http://stackoverflow.com/a/38192468/5562328
-- thanks kmario23.
"""


import time, argparse, os, sys, json

from social_media_auth import Trump_client

#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from http.client import IncompleteRead


consumer_key = Trump_client['consumer_key']
consumer_secret = Trump_client['consumer_secret']
access_token = Trump_client['access_token']
access_token_secret = Trump_client['access_token_secret']

Trump_twitter_accounts = ['25073877', '822215679726100480']     # @realDonaldTrump = 25073877; @POTUS = 822215679726100480
# Trump_twitter_accounts = ['814046047546679296']               # @false_trump = 814046047546679296

class StdOutListener(StreamListener):
    '''A basic listener that just writes received tweets to file.'''

    def __init__(self):
        StreamListener.__init__(self)

    def on_data(self, data):
        data = json.loads(data)
        if data['user']['id_str'] in Trump_twitter_accounts:
            print(data['text'])
        return True

    def on_error(self, status):
        print(status)


if __name__ == '__main__':
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

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