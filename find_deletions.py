#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This is a script that searches through the archives created by the archive_junta
script and checks each archived tweet to see if it is still available. If it is
not, then the tweet has been deleted, and it is added to a list of deleted
tweets (the location is configurable below with the constant
DELETED_TWEETS_LIST).

This quick hack wound up being necessary because I did not initially track
deleted tweets, although I wish I had. Recent versions of archive_junta.py do
in fact keep track of which tweets have been deleted, so hopefully this script
is only necessary to go back and do the work that the primary script should
have done from the beginning. (Although, come to think of it, maybe I should
still run this periodically and make sure nothing has been missed.)

This program is free software, licensed under the GPL, either version 3, or (at
your choice) any later version, and you are welcome to modify or redistribute
it, subject to certain requirements; see the file LICENSE.md for more info.

This program is alpha software. You are welcome to use it, but assume all risk
incurred by doing so. The author assumes no liability for any damages that this
script may do to your computer or data or other valuables, and makes no
guarantees about the performance of this software -- not even the guarantee of
merchantability or fitness for any particular purpose. In no case will the
author be liable for damages in excess of the purchase price you have paid for
this program.
"""


import csv, requests


home_dir = '/archive-junta'
data_dir = '%s/data' % home_dir
deleted_tweets_list = '%s/found_deleted_tweets.csv' % data_dir


