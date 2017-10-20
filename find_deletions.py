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


import csv, datetime, glob, os, requests
import patrick_logger                               # https://github.com/patrick-brian-mooney/python-personal-library/


home_dir = '/archive-junta'
data_dir = '%s/data' % home_dir
deleted_tweets_list = '%s/found_deleted_tweets.csv' % home_dir


patrick_logger.verbosity_level = 5
log = patrick_logger.Logger(name='find_deletions.py', logfile_paths = [ "%s/logs/find_deletions.py run on %s.log" % (home_dir, str(datetime.datetime.now())) ])


log.log_it("We're starting...")


def tweet_is_live(archival_url):
    """Returns True if the tweet that was archived at ARCHIVAL_URL is still live on
    Twitter; False if it is not.
    """
    return True     #FIXME


if os.path.exists(deleted_tweets_list):
    deleted_tweets_file = open(deleted_tweets_list, 'a', newline='')
    csvwriter = csv.writer(deleted_tweets_file, dialect='unix')
    log.log_it("INFO: successfully opened existing deleted tweets file for appending at %s." % deleted_tweets_list)
else:
    deleted_tweets_file = open(deleted_tweets_list, 'w', newline='')
    csvwriter = csv.writer(deleted_tweets_file, dialect='unix')
    csvwriter.writerow(['user ID', 'tweet ID', 'tweet text', 'archive URL', 'time deletion noticed'])
    log.log_it("INFO: successfully created new deleted tweets file at %s." % deleted_tweets_list)

for which_archive in sorted(glob.glob('%s/archive_*csv' % data_dir)):
    log.log_it("\n\nINFO: about to begin searching for deletions in %s:" % which_archive)
    with open(which_archive, 'r', newline='') as current_archive_file:
        reader = csv.reader(current_archive_file, dialect='unix')
        known_tweet_list = list(reader)
        # Note that format here is a list of lists [['tweet', 'http://archived_tweet_URL'], ['(the same) tweet', 'https://archived_tweet_url'], ... ]
        # In retrospect, I don't mind admitting I wish I'd tracked just a bit more data for each entry in the list.
    for line_number, line in enumerate(known_tweet_list):
        log.log_it(" INFO: we're looking at line # %d" % line_number, 2)
        log.log_it('    ... contents of that line are: "%s" (length %d).' % (line, len(line)), 2)
        tweet, archive_url = line
        log.log_it("  INFO: we're checking for the tweet '%s' ..." % tweet, 3)
        if not tweet_is_live(archive_url):
            log.log_it("    --not found! Adding to deleted tweets list ...", 3)
            username = which_archive.strip().lstrip(data_dir).strip().lstrip('archive_').strip().rstrip('.csv').strip()
            tweet_id = archive_url.strip().lstrip('http://').lstrip('https://').strip().lstrip('web.archive.org/*/').lstrip('http://').lstrip('https://')
            tweet_id = tweet_id.strip().lstrip('twitter.com/').lstrip(username).lstrip('/status/').strip()
            csvwriter.writerow([ username, tweet_id, tweet, archive_url, str(datetime.datetime.now()) ])
            log.log_it("         ...done.", 5)
        else:
            log.log_it("    --found!", 4)
        
deleted_tweets_file.close()