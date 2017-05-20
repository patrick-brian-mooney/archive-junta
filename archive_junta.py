#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This script uses the Twitter streaming API to wait for tweets by Donald Trump,
then causes them to be archived at the Internet Archive, hopefully before The
Donald deletes them.

First steps here were based partly on a reading of the question and answers at
http://stackoverflow.com/a/38192468/5562328 -- thanks kmario23 for pointing me
in the right direction.

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


import time, json, requests, sys, pprint, csv, os
import _thread

from tweepy.streaming import StreamListener                     # http://www.tweepy.org
from tweepy import OAuthHandler
from tweepy import Stream
from http.client import IncompleteRead

import pid                                                      # https://pypi.python.org/pypi/pid/


import patrick_logger                                           # https://github.com/patrick-brian-mooney/python-personal-library/
import social_media as sm                                       # https://github.com/patrick-brian-mooney/python-personal-library/
from social_media_auth import Trump_client, Trump_client_for_personal_account   # Unshared module that contains my authentication constants

consumer_key, consumer_secret = Trump_client['consumer_key'], Trump_client['consumer_secret']
access_token, access_token_secret = Trump_client['access_token'], Trump_client['access_token_secret']

target_accounts = { #First, the president 
                    '25073877': 'realDonaldTrump',
                    '822215679726100480': 'POTUS',
                    # And the VP
                    '22203756': 'mike_pence',
                    '15985455': 'GovPenceIN',
                    '818910970567344128': 'VP',
                    # And Dan Scavino Jr., Trump's current director of social media, who writes many WH tweets 
                    '823367015830323201': 'Scavino45',
                    '620571475': 'DanScavino',
                    # Melania Trump
                    '823367015830323201': 'FLOTUS',
                    '108471631': 'MELANIATRUMP',
                    # Ivanka Trump
                    '52544275': 'IvankaTrump',
                    '798195585824104449': 'IvankaTrumpHQ',
                    # Jared Kushner, senior adviser to Drumpf and presumptive banger of Ivanka
                    '29547260': 'jaredkushner',
                    # Paul Ryan, speaker of the House
                    '18916432': 'SpeakerRyan',
                    '733751245': 'PRyan',
                    # AshLee Strong, press secretary for Paul Ryan
                    '296060169': 'AshLeeStrong',
                    # Some extra accounts of my own for script testing
                    # '814046047546679296': 'false_trump',
                    # '2268719071': 'IrishLitTweets',
                  }
archiving_url_prefixes = ['http://web.archive.org/save/']

home_dir = '/archive-junta'
data_dir = '%s/data/' % home_dir
last_tweet_id_store = '%s/last_tweet' % data_dir

patrick_logger.verbosity_level = 1

tweet_about_deletions = True


# OK, let's work around a problem that comes from the confluence of Debian's ancient packaging and rapid changes in Python's Requests package.
try:
    x = ProtocolError               # Test for existence.
    patrick_logger.log_it('NOTE: We are running on a system where ProtocolError is properly defined', 2)
except Exception as e:              # If it's not defined, try to import it.
    try:
        patrick_logger.log_it('WARNING: no ProtocolError (got exception "%s"); trying from requests.packages.urllib3.exceptions instead' % e)
        from requests.packages.urllib3.exceptions import ProtocolError
        patrick_logger.log_it('NOTE: successfully imported from requests')
    except Exception as e:
        try:
            patrick_logger.log_it('WARNING: still got exception "%s"; trying from xmlrpclib instead' % e)
            from xmlrpclib import ProtocolError
            patrick_logger.log_it('NOTE: successfully imported from xmlprclib')
        except Exception as e:      # If we can't import it, define it so the main loop's Except clause doesn't crash on every exception.
            patrick_logger.log_it('WARNING: still got exception "%s"; defining by fiat instead' % e)
            ProtocolError = IncompleteRead


logger_lock = _thread.allocate_lock()

def log_it(*pargs, **kwargs):
    """Just a thread-safe wrapper for patrick_logger.log_it."""
    logger_lock.acquire()
    patrick_logger.log_it(*pargs, **kwargs)
    logger_lock.release()
    
def exclusive_open(path, *pargs, **kwargs):
    """Open a file exclusively for read/write access, blocking until it's available to
    be exclusively opened.
    """
    fd_file = os.open(path, (os.O_RDWR | os.O_EXCL))
    return os.fdopen(fd_file, 'r+', *pargs, **kwargs)


def get_tweet_urls(username, id):
    """Return all of the relevant URLs of the specified tweet. Currently, this
    just means that the http:// and https:// versions are returned.
    """
    ret = "twitter.com/%s/status/%s" % (username, id)
    return ("http://" + ret, "https://" + ret)

def archive_tweet(screen_name, id, text):
    """Have the Internet Archive (and in the future, perhaps, other archives) save
    a copy of this tweet.
    
    Should be thread-safe, so it can be = called from the main Listener object and
    won't block its operations. This should help both to avoid missing other tweets
    on other accounts and avoid having Twitter kill us off for being too slow. 
    """
    log_it("New tweet from %s: %s" % (screen_name, text), 0)
    for which_url in get_tweet_urls(screen_name, id):
        log_it("\narchiving URL %s" % which_url, 0)
        for which_prefix in archiving_url_prefixes:
            log_it("    ... archiving using prefix %s" % which_prefix)
            read_it = False
            while not read_it:
                sleep_interval = 5
                try:
                    req = requests.get(which_prefix + which_url)
                    for the_item in req.iter_content(chunk_size=100000): pass   # read the file to make the IArchive archive it.
                    read_it = True
                except (IncompleteRead, requests.exceptions.ConnectionError) as e:
                    if sleep_interval >= 300:   # Give up
                        raise e("Unable to archive tweet even with wait of five minutes")
                    log_it("WARNING: attempt to archive timed out, sleeping for %d seconds" % sleep_interval)
                    time.sleep(sleep_interval)
                    sleep_interval *= 1.5      # Keep sleeping longer and longer until it works
                    continue
            # Now add it to the publicly visible list of tweets we've archived
            try:
                csvfile = exclusive_open('%s/archive_%s.csv' % (data_dir, screen_name), newline='')
                csvfile.seek(0, 2)      # Seek to end of file
                csvwriter = csv.writer(csvfile, dialect='unix')
                csvwriter.writerow([text, which_prefix.replace('/save/', '/*/') + which_url])
            finally:
                csvfile.close()
    try:
        store = exclusive_open("%s.%s" % (last_tweet_id_store, screen_name))
    except FileNotFoundError:
        with open("%s.%s" % (last_tweet_id_store, screen_name), mode="w") as store:
            store.write('-1')
        store = exclusive_open("%s.%s" % (last_tweet_id_store, screen_name), mode="r+")
    try:
        if int(store.read()) < int(id):     # If this is a newer tweet we're getting, store its ID as the newest tweet seen.
            store.seek(0)
            store.write(id)
    except (TypeError, ValueError):
        store.seek(0)
        store.write(id)
    store.close()


class FascistListener(StreamListener):
    """Donald Trump is an abusive, sexist, racist, jingoistic pseudo-fascist. Mike
    Pence is even worse. It's best to avoid actually paying attention to what
    they write. Let's create a bot to listen for us.
    """
    def on_data(self, data):
        try:
            data = json.loads(data)
            try:
                if data['user']['id_str'] in target_accounts:        # If it's one of the accounts we're watching, archive it.
                    _ = _thread.start_new_thread(archive_tweet, (data['user']['screen_name'], data['id_str'], data['text']))
            except KeyError:
                log_it('WARNING: we got minimal data again', 1)
                log_it('Value of data is:', 1)
                log_it(pprint.pformat(data), 1)
                if 'delete' in data:
                    log_it("OK, it's a deletion", 1)
                    if tweet_about_deletions:
                        try:
                            log_it(" ... and we're going to tweet about it", 1)
                            username = target_accounts[data['delete']['status']['user_id_str']]
                            tweet_id = data['delete']['status']['id_str']
                            archived_url = 'http://web.archive.org/web/*/https://twitter.com/%s/status/%s' % (username, tweet_id)
                            the_tweet="Looks like **%s** just deleted a tweet. There might be an archived copy at %s, though."
                            the_tweet = the_tweet % (username, archived_url)
                            sm.post_tweet(the_tweet=the_tweet, client_credentials=Trump_client_for_personal_account)
                        except KeyError:
                            pass            # Well, Twitter didn't give us enough info to say anything about it, did they?
        except:
            log_it('ERROR: \n  Exception is:', -1)
            log_it(pprint.pformat(sys.exc_info()[0]), -1)
            log_it('  Value of data is:', -1)
            log_it(pprint.pformat(data), -1)
            raise
        return True
    
    def on_error(self, status):
        log_it("ERROR: %s" % status, 0)


# This next group of functions handles the downloading, processing, and storing of The Donald's tweets.
def get_new_tweets(screen_name, oldest=-1):
    """Get those tweets newer than the tweet whose ID is specified as the OLDEST
    parameter from the account SCREEN_NAME.
    """
    the_API = sm.get_new_twitter_API(Trump_client)
    # get most recent tweets (200 is maximum possible at once)
    new_tweets = the_API.user_timeline(screen_name=screen_name, count=200)
    ret = new_tweets.copy()

    try:
        oldest_tweet = ret[-1].id - 1   # save the id of the tweet before the oldest tweet
    except IndexError:
        oldest_tweet = -1               # Don't crash if someone has NEVER tweeted.

    # keep grabbing tweets until there are no tweets left
    while len(new_tweets) > 0 and oldest < new_tweets[0].id:
        log_it("getting all tweets before ID #%s" % oldest_tweet, 0)
        new_tweets = the_API.user_timeline(screen_name=screen_name, count=200, max_id=oldest_tweet)
        ret.extend(new_tweets)
        oldest_tweet = ret[-1].id - 1
        log_it("    ...%s tweets downloaded so far" % (len(ret)), 0)
    return [t for t in ret if (t.id > oldest)]

def do_archive_tweets(the_tweets):
    """Send each unarchived tweet to each archiving service that the script knows about.
    (At the time of this writing, the only known archiving service is the Internet
    Archive.) Each instance of this function will be started in a separate thread to
    help avoid the possibility that adding a new account to archive delays looking
    at other accounts long enough for tweets on those accounts to disappear before
    they're archived.
    
    the_tweets is a list of tweepy.Tweet objects. 
    """
    for tw in the_tweets:
        archive_tweet(tw.user.screen_name, tw.id_str, tw.text)
        time.sleep(1)

def startup():
    """Perform startup tasks. Currently, this means:

        1. archive any tweets we may have missed between now and whenever we last
           stopped running.
        2. that's it. Nothing else.
    """
    log_it('Starting up...', 0)
    for id, username in target_accounts.items():
        try:
            with open("%s.%s" % (last_tweet_id_store, username)) as store:
                newest_id = int(store.read())
        except FileNotFoundError:
            with open("%s.%s" % (last_tweet_id_store, username), mode="w") as store:
                store.write("-1")
            newest_id = -1
        log_it("about to get all tweets newer than ID #%s for account @%s" % (newest_id, username))
        new_tweets = sorted([t for t in get_new_tweets(screen_name=username, oldest=newest_id) if t.id > newest_id], key=lambda t: t.id)
        if new_tweets:
            _ = _thread.start_new_thread(do_archive_tweets, (new_tweets, ))

if __name__ == '__main__':
    try:
        with pid.PidFile(piddir=home_dir):
            startup()
            l = FascistListener()
            auth = OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            log_it("... OK, we're set up, and about to watch %s" % ', '.join(target_accounts), 0)
            while True:
                try:
                    stream = Stream(auth, l)
                    stream.filter(follow=target_accounts, stall_warnings=True)
                except (IncompleteRead, ProtocolError, requests.packages.urllib3.exceptions.ReadTimeoutError) as e:
                    # Sleep some before trying again.
                    patrick_logger.log_it("WARNING: received error %s; sleeping and trying again ..." % e)
                    time.sleep(15)
                    continue
                except KeyboardInterrupt:
                    stream.disconnect()
                    break
    except pid.PidFileError:
        log_it("Already running! Quitting ...", 0)
        sys.exit()
