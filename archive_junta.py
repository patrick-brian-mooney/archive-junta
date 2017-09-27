#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This script uses the Twitter streaming API to wait for tweets by Donald Trump,
then causes them to be archived at the Internet Archive, hopefully before The
Donald deletes them. It also follows other members of the currently ruling
American corporatist junta. More information and an index to archived tweets is
available at https://is.gd/fascist_archiver.

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


import csv, datetime, json, os, pprint, requests, sys, time
import _thread

from tweepy.streaming import StreamListener                     # http://www.tweepy.org
from tweepy import OAuthHandler
from tweepy import Stream
from http.client import IncompleteRead

import pid                                                      # https://pypi.python.org/pypi/pid/


import patrick_logger                                           # https://github.com/patrick-brian-mooney/python-personal-library/
import social_media as sm                                       # https://github.com/patrick-brian-mooney/python-personal-library/
from social_media_auth import Trump_client, Trump_client_for_personal_account   # Unshared module that contains my authentication constants

home_dir = '/archive-junta'
data_dir = '%s/data' % home_dir
last_tweet_id_store = '%s/last_tweet' % data_dir
log_directory = '%s/logs' % home_dir
unhandled_data_dir = '%s/unhandled_data' % home_dir
unrecorded_dels_dir = '%s/unrecorded_deletions' % unhandled_data_dir

target_accounts_data = "%s/tracked_users_data.csv" % data_dir
webpage_loc = '/~patrick/projects/FascistTweetArchiver/index.html'

consumer_key, consumer_secret = Trump_client['consumer_key'], Trump_client['consumer_secret']
access_token, access_token_secret = Trump_client['access_token'], Trump_client['access_token_secret']

patrick_logger.verbosity_level = 2
log = patrick_logger.Logger(name='Fascist Tweet Archiver', logfile_paths = [ "%s/%s.log" % (log_directory, str(datetime.datetime.now())) ])
logger_lock = _thread.allocate_lock()

def log_it(*pargs, **kwargs):
    """Just a thread-safe wrapper for patrick_logger.log_it."""
    logger_lock.acquire()
    log.log_it(*pargs, **kwargs)
    logger_lock.release()


with open(target_accounts_data, mode='rt', newline='') as infile:
    reader = csv.reader(infile, dialect='unix')
    next(reader)                                # Skip the header line
    target_accounts = {rows[0]:rows[1] for rows in reader}
    log_it("INFO: read target account data; we're tracking %d accounts" % len(target_accounts), 1)

notify_on_delete_accounts = ['realDonaldTrump',  'POTUS', 'WhiteHouse', ]   # Currently, we're only tweeting about Trump's own deletions.

archiving_url_prefixes = ['http://web.archive.org/save/', ]

patrick_logger.verbosity_level = 3

tweet_about_deletions = True


# OK, let's work around a problem that comes from the confluence of Debian's ancient packaging and rapid changes in Python's Requests package.
try:
    x = ProtocolError               # Test for existence.
    log_it('NOTE: We are running on a system where ProtocolError is properly defined', 2)
except Exception as e:              # If it's not defined, try to import it.
    try:
        log_it('WARNING: no ProtocolError (got exception "%s"); trying requests.packages.urllib3.exceptions instead' % e)
        from requests.packages.urllib3.exceptions import ProtocolError
        log_it('NOTE: successfully imported from requests')
    except Exception as e:
        try:
            log_it('WARNING: still got exception "%s"; trying from xmlrpclib instead' % e)
            from xmlrpclib import ProtocolError
            log_it('NOTE: successfully imported from xmlprclib')
        except Exception as e:      # If we can't import it, define it so the main loop's Except clause doesn't crash on every exception.
            log_it('WARNING: still got exception "%s"; defining by fiat instead' % e)
            ProtocolError = IncompleteRead


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

    Should be thread-safe, so it can be called from the main Listener object and
    won't block its operations. This should help both to avoid missing other tweets
    on other accounts and avoid having Twitter kill us off for being too slow.
    """
    log_it("\n\nNew tweet from %s: %s" % (screen_name, text), 0)
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
                try:
                    csvfile = exclusive_open('%s/archive_%s.csv' % (data_dir, screen_name), newline='')
                except FileNotFoundError:
                    with open('%s/archive_%s.csv' % (data_dir, screen_name), mode="w"):     # Create the file
                        '%s/archive_%s.csv' % (data_dir, screen_name)
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

def get_archived_tweet(username, id):
    """Given the USERNAME and ID (both strings) of a tweet, get that tweet from the archive
    for tracked user USERNAME, if we archived it. Returns a tuple:
        (full text of original tweet, archive URL for that tweet)
    If we never archived the tweet: returns (None, None)
    """
    log_it("INFO: get_archived_tweet() called to get tweet ID %s for account %s" % (id, username))
    with open('%s/archive_%s.csv' % (data_dir, username), newline='') as archive_file:
        reader = csv.reader(archive_file)
        for line in reader:
            try:
                full_text, archive_url, *_ = line
                if id in archive_url:
                    log_it("INFO: found a tweet!\t\t%s\t%s" % (archive_url, full_text), 2)
                    return full_text, archive_url
            except BaseException as e:
                log_it('ERROR: unable to read line "%s" because: %s.' % (line, e))
                continue
    log_it("INFO: requested tweet not found in relevant archive")
    return None, None

def handle_deletion(data):
    """Take any necessary action when Twitter reports a tweet has been deleted. Currently,
    we do two things here: one, add the tweet (and as much information about it as
    possible) to a .csv file collecting delted tweets; and two, possibly tweet about
    it on my personal Twitter account.
    """
    log_it('INFO: handling a deletion for data:\n\n%s' % pprint.pformat(data))
    json_filename = "%s/%s.json" % (unrecorded_dels_dir, str(datetime.datetime.now()))
    with open(json_filename, mode="w") as json_file:
        json_file.write(json.dumps(data))
    log_it('INFO: successfully dumped raw data to JSON file')
    try:
        username = target_accounts[data['delete']['status']['user_id_str']]
        tweet_id = data['delete']['status']['id_str']
        log_it("INFO: We're handling a deletion notification for tweet ID# %s on account %s" % (tweet_id, username), 1)
        tweet_text, archived_url = get_archived_tweet(username, tweet_id)
        try:
            log_it('... adding to list of deleted tweets', 1)
            csvfile = exclusive_open('%s/deleted_tweets.csv' % data_dir, newline='')
            csvfile.seek(0, 2)      # Seek to end of file
            csvwriter = csv.writer(csvfile, dialect='unix')
            csvwriter.writerow([username, tweet_id, tweet_text, archived_url, str(datetime.datetime.now())])
            log_it('... added', 1)
        finally:
            csvfile.close()
        os.unlink(json_filename)        # If we've made it this far, it's no longer unrecorded.
        if tweet_about_deletions:
            if username in notify_on_delete_accounts:
                log_it(" ... and we're going to tweet about it", 1)
                the_tweet = "Looks like **%s** just deleted a tweet. There might be an archived copy at %s, though."
                the_tweet = the_tweet % (username, archived_url)
                sm.post_tweet(the_tweet=the_tweet, client_credentials=Trump_client_for_personal_account)
            else:
                log_it("... but we're not going to tweet about it because %s is not in the list of accounts we tweet about" % username, 1)
        else:
            log_it("... but we're not going to tweet about it because tweet_about_deletions is False", 1)
    except KeyError:
        log_it('ERROR: unable to handle deletion notification (Twitter passed us incomplete data?): %s' % pprint.pformat(data), 1)


class FascistListener(StreamListener):
    """Donald Trump is an abusive, sexist, racist, jingoistic pseudo-fascist. Mike
    Pence is even worse. The rest of the group is no treat, either. It's best to
    avoid actually paying attention to what they write. Let's create a bot to
    listen for us.
    """
    def on_data(self, data):
        try:
            data = json.loads(data)
            try:
                if data['user']['id_str'] in target_accounts:        # If it's one of the accounts we're watching, archive it.
                    _ = _thread.start_new_thread(archive_tweet, (data['user']['screen_name'], data['id_str'], data['text']))
            except KeyError:
                 if 'delete' in data:
                     handle_deletion(data)
                 else:
                    log_it('INFO: we got minimal data again', 1)
                    log_it('... value of data is:\n\n%s\n\n' % pprint.pformat(data), 1)
                    log_it('... attempting to archive ...', 1)
                    json_filename = "%s/%s [%s].json" % (unhandled_data_dir, str(datetime.datetime.now()), ', '.join(list(data.keys())))
                    with open(json_filename, mode="w") as json_file:
                        json_file.write(json.dumps(data))
        except:
            log_it('ERROR: \n  Exception is:', -1)
            log_it(pprint.pformat(sys.exc_info()[0]), -1)
            log_it('  Value of data is:', -1)
            log_it(pprint.pformat(data), -1)
            raise
        return True

    def on_error(self, status):
        log_it("ERROR: %s" % status, 0)


# This next group of functions handles the downloading, processing, and storing of tweets.
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

    THE_TWEETS is a list of tweepy.Tweet objects.
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
                    log_it("WARNING: received error %s; sleeping and trying again ..." % e)
                    time.sleep(15)
                    continue
                except KeyboardInterrupt:
                    stream.disconnect()
                    break
    except pid.PidFileError:
        log_it("Already running! Quitting ...", 0)
        # But first, delete the small log file we may have created.
        paths = log.logfile_paths
        del(log)
        if paths:
            for path in paths:
                try:
                    os.unlink(path)
                except Exception as e:
                    print("ERROR: unable to delete %s" % path)
                    print("The system said: %s" % e)
        sys.exit()


def export_web_page():
    """Exports a web page to the location specified by the global constant WEBPAGE_LOC.
    This function is NEVER called by the script itself; it's a utility function
    intended for use from the interactive Python console.
    
    So the process for adding a new account to those watched by the script goes
    like this:
        1. Editing tracked_users_data.csv to add info about the account, leaving
           the URL fields blank; 
        2. Restarting the script so that it re-reads the data and begins archiving
           the new account(s);
        3. Waiting for enough of the archiving to complete that there all of the
           necessary files have been generated and archived (uploaded to DropBox,
           archived in GitHub, etc.) so that the appropriate URLs have been
           created and can be found;
        4. Adding the relevant URLs to users_data.csv;
        5. From an interactive Python console, importing the script and running
           this function right here;
        6. Uploading the newly generated page to my web server.
    """
    the_page = """<!doctype html>
<html prefix="og: http://ogp.me/ns#" xml:lang="en" lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta name="generator" content="Bluefish 2.2.9" />
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="/~patrick/css/skeleton-normalize.css" />
  <link rel="stylesheet" type="text/css" href="/~patrick/css/skeleton.css" />
  <link rel="stylesheet" type="text/css" href="/~patrick/css/content-skel.css" />
  <link rel="meta" type="application/rdf+xml" title="FOAF" href="/~patrick/foaf.rdf" />
  <meta name="foaf:maker" content="foaf:mbox_sha1sum '48a3091d919c5e75a5b21d2f18164eb4d38ef2cd'" />
  <link rel="profile" href="http://microformats.org/profile/hcard" />
  <link rel="profile" href="http://microformats.org/profile/hcalendar" />
  <link rel="profile" href="http://gmpg.org/xfn/11" />
  <link rel="pgpkey" type="application/pgp-keys" href="/~patrick/505AB18E-public.asc" />
  <link rel="me" href="http://plus.google.com/109251121115002208129?rel=author" />
  <link rel="home" href="/~patrick/" title="Home page" />
  <link rel="icon" type="image/x-icon" href="/~patrick/icons/favicon.ico" />
  <link href="/~patrick/feeds/updates.xml" type="application/atom+xml" rel="alternate" title="Sitewide ATOM Feed" />

  <title>archive_junta.py, the Fascist-Tweet-Archiving Script</title>
  <meta name="author" content="Patrick Mooney" />
  <meta name="dcterms.rights" content="Copyright © 2017 Patrick Mooney" />
  <meta name="description" content="A script that backs up Donald Trump's and his cadre's tweets to the Internet Archive" />
  <meta name="rating" content="general" />
  <meta name="revisit-after" content="7 days" />
  <meta name="%s" content="%s" />
  <meta property="fb:admins" content="100006098197123" />
  <meta property="og:title" content="archive_junta.py, the Fascist-Tweet-Archiving Script" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="http://patrickbrianmooney.nfshost.com/~patrick/projects/FascistArchiver/" />
  <meta property="og:image" content="http://patrickbrianmooney.nfshost.com/~patrick/icons/gear.png" />
  <meta property="og:description" content="A script that backs up Donald Trump's and his cadre's tweets to the Internet Archive" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:site" content="@patrick_mooney" />
  <meta name="twitter:creator" content="@patrick_mooney" />
  <meta name="twitter:title" content="archive_junta.py, the Fascist-Tweet-Archiving Script" />
  <meta name="twitter:description" content="A script that backs up Donald Trump's and his cadre's tweets to the Internet Archive" />
  <meta name="twitter:image:src" content="http://patrickbrianmooney.nfshost.com/~patrick/icons/gear.png" />
</head>
""" % ('date', datetime.datetime.now().isoformat())
    the_page += """  <body lang="en-US" xml:lang="en-US"><div class="container">
  <!-- Begin navigation and tracking code -->
  <header id="main-nav">
    <script type="text/javascript" src="/~patrick/nav.js"></script>
    <noscript>
        <p class="simpleNav"><a rel="me home" href="index.html">Go home</a></p>
        <p class="simpleNav">If you had JavaScript turned on, you'd have more navigation options.</p>
    </noscript> 
    <script type="text/javascript">
      var _gaq = _gaq || [];
      _gaq.push(['_setAccount', 'UA-37778547-1']);
      _gaq.push(['_setDomainName', 'nfshost.com']);
      _gaq.push(['_setAllowLinker', true]);
      _gaq.push(['_trackPageview']);
    
      (function() {
      var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
      ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
      var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      })();
    </script>
</header>
<!-- End navigation and tracking code -->

<h1><code>archive_junta.py</code>, the Fascist-Tweet-Archiving Script</h1>

<h2 id="overview">Overview</h2>

<p>The <a rel="me" href="https://github.com/patrick-brian-mooney/archive-trump"><code>archive_junta.py</code> script</a> runs on one of my spare laptops, constantly listening for new tweets on certain Twitter accounts associated with specific members of the current American corporatist junta. When new tweets on those accounts occur, it uses the Internet Archive to create an offsite copy of those tweets. At the beginning, it just watched Donald Trump's Twitter accounts; but I've been gradually expanding, in a non-systematic way, the scope of its areas of attention.</p>

<p>The full list of accounts currently archived the operation of this script on my spare laptop is:</p>

<table class="vcalendar">
    <tr><th scope="col">Account</th><th scope="col">Date archiving began</th><th scope="col">Dropbox index<br />(most up-to-date)</th><th scope="col">GitHub index<br />(easier to read)</th><th scope="col">Search<br />(via Internet Archive)</th><th scope="col">Notes</th></tr>""" 

    with open(target_accounts_data, mode='rt', newline='') as infile:
        reader = csv.reader(infile, dialect='unix')
        header = next(reader)                                # Skip the header line
        for the_row in reader:
            the_row = dict(zip(header, the_row))
            if the_row['IA search'] and the_row['GitHub index'] and the_row['DropBox index']:
                the_page += """\n    <tr class="vevent"><td><abbr class="summary description" title="Tweet archiving began for @%s"><a rel="nofollow" href="http://twitter.com/%s">@%s</a></abbr></td><td><abbr class="dtstart" title="%s">%s</abbr></td> <td><a href="%s">here</a></td> <td><a href="%s">here</a></td> <td><a href="%s">here</a></td> <td>%s</td></tr>""" % (the_row['username'], the_row['username'], the_row['username'], the_row['ISO date'], the_row['text date'], the_row['DropBox index'], the_row['GitHub index'], the_row['IA search'], the_row['description'])
            else:
                the_page += """\n    <tr class="vevent"><td><abbr class="summary description" title="Tweet archiving began for @%s"><a rel="nofollow" href="https://twitter.com/%s">@%s</a></abbr></td><td><abbr class="dtstart" title="%s">%s</abbr></td> <td colspan="3" style="text-align:center">(has not yet tweeted)</td> <td>%s</td></tr>""" % (the_row['username'], the_row['username'], the_row['username'], the_row['ISO date'], the_row['text date'], the_row['description'])
    
    the_page += """</table>
\n\n<p>My intent is to get a neutral third party to create publicly accessible backups of the tweets before they can be deleted, because a neutral third-party archive is a more credible source than a screenshot that I produced on my own computer and totally swear I didn't alter. (It's also easier to produce automatically.)</p>

<h2 id="missed-someone"><q>Hey, there's someone who should be in the list above, but isn't!</q></h2>

<p>Please <a rel="me" href="https://twitter.com/patrick_mooney">contact me on Twitter</a> and give me their verified Twitter account names.</p>

<h2 id="where-archives"><q>Where can I see the tweets archived by your script?</q></h2>

<p>The script produces an index for each account it tracks as it runs. These indices are in the <code>.csv</code> format, which is easily importable into any spreadsheet program; they are hosted both on Dropbox and at the project's GitHub page. (The Dropbox-hosted copies should usually be automatically updated within a minute or so; the GitHub-hosted copies are easier to read from the web, but are usually only updated about once a day.) You can also search through the Internet Archive-hosted tweets using the Internet Archive's interface. Links to all of these options are available in the table above.</p>

<p>If you are unhappy with the display options, it's probably wisest to download the current .csv from Dropbox and search through it using your favorite spreadsheet program. Currently, it's not possible to search deleted tweets from this page, but if you want make an offer to finance hosting such a service, we can talk.</p> 

<p>If you want to see a tweet from me every time the script detects a deleted tweet from the junta, you can <a rel="me author" href="https://twitter.com/patrick_mooney">follow me</a> on Twitter.</p>

<h2 id="why-would-you"><q>Why would you even bother to get a machine to archive these tweets in the first place?</q></h2>

<p>Because words matter, especially the words spoken by elected officials; they have wide-ranging effects even after their material presence has evaporated into the ether. Donnie's profound contempt for facts and his repeated insistence on inventing them are both troubling, and I suspect that there's a connection with the surprisingly frequent deletion of his own posts on Twitter.</p>

<p>When The Donald deletes a tweet, that doesn't mean that the deleted words have had no effect; they still influence the thoughts and behavior of (at least some of) his supporters. All it really means is that the effect is harder to trace back to the suddenly absent cause. My thought is that producing an archive that's accessible to the public at an external source helps to reinforce, in a small way, the underlying discursive structures upon which a functioning democracy depends.</p>

<h2 id="why-do-you-think"><q>What do you think it means that Little Don-Don and his friends delete their tweets?</q></h2>

<p>I think that depends entirely on which tweet we're talking about.</p>

<p>You will note that I have not claimed that tweets should never be deleted, nor that the removal of any particular post necessarily means anything that I'm qualified to talk about. You may also note that I have sometimes deleted my own tweets, usually&mdash;but not always&mdash;to correct a typographical error. (But then, I am not a government official, and so the standard for me is lower than it is for someone who has been given a large amount of public trust.) In any case, I think that preserving an archive of what our current president and his cadre say is very important, and it's relatively easy to do.</p>

<h2 id="should-i"><q>Should I myself run a copy of this script?</q></h2>

<p>Maybe! As for me, I'm just running the script on a spare laptop in my apartment, and that's not a perfect setup: my electricity or Internet service could go out, or the laptop could overheat, or its old hardware might be running the script too slowly to catch a tweet before it's erased, or any number of other things could go wrong. Having several people&mdash;certainly more than a dozen or so would be overkill&mdash;all running this script (or taking similar actions) would provide a level of redundancy that would help to make always capturing every tweet at least once much more likely.</p>

<p>On the other hand, if <em>way too many people</em> decide to volunteer in this way, that would unnecessarily burden the infrastructures of both the Internet Archive and Twitter for little to no practical benefit. So my suggestion is this: if you plan to run another copy of this script, let me know (hit me up <a rel="me" href="https://twitter.com/patrick_mooney">on Twitter</a>), and I'll keep an up-to-date count (and/or tally) here.</p>

<p>To the best of my knowledge, there are currently <strong>no other people</strong> running this script remotely.</p>

<p>Given all of that, you can download the script <a rel="me" href="https://github.com/patrick-brian-mooney/archive-junta">on GitHub</a>, if you'd like.</p>

<h2 id="does-your-script-ensure"><q>Does this script ensure there is a complete archive of all of Trump's (and the others') tweets?</q></h2>

<p>No. There are at least two groups of tweets that the script is not archiving:</p>

<ol>
    <li><strong>Very old tweets.</strong> The Twitter API only allows access to someone's last 3200 or so tweets, so the first tweet this script archived was probably produced by Donnie somewhere around March 2016. I have not made any attempt to go back and algorithmically save older Trump tweets, in part because that would require a totally different methodology, and quite possibly substantial manual intervention. (There <em>are</em> older Trump tweets archived on the Internet Archive, but they were not saved by this script.)</li>
    <li><strong>Tweets that both appear and disappear while the script is not running.</strong> Normally, the script runs constantly, but if the power goes off in my apartment, or if the script crashes, and Donnie tweets and then deletes that tweet before the script runs again, then the tweet won't get archived. Similarly, it is possible that a tweet could get noticed but still disappear before it <em>can</em> be archived.</li>
</ol>

<p>There are at least two other groups of potential problems that might, in theory, keep a tweet from being archived:</p>

<ol>
    <li>The Twitter API could, in theory, not report that a tweet was posted, or could do so with a large enough delay to allow Donnie or his goony henchmen to delete it before it could be archived.</li>
    <li>It is possible, in theory, that Creepy Don or his servile brownshirt brigade might interfere with one or more of the services required for this to work.</li>
</ol>

<p>I don't currently have cause to believe that anything has been missed for any of the reasons above except for <q>very old tweets</q> ... but then, if it did, how would I know? (This is part of why the reason why the redunancy of several other people running the script would be a good thing.)</p>

<h2 id="were-all-of-the"><q>Were all of the tweets I can see on the Internet Archive for these accounts saved by your script?</q></h2>

<p>No. Anyone can save a web page to the Internet Archive at any time, and I am certainly not the only person who has decided to have the Internet Archive save copies of (some of) the junta's tweets. (Though, to the best of my knowledge, I am the first to think that doing so systematically is a good idea.)</p>

<h2 id="how-does-it-work"><q>How does it work?</q></h2>

<p>Head on over to <a rel="me" href="https://github.com/patrick-brian-mooney/archive-trump">the GitHub project</a> for more info!</p>

<footer class="status vevent vcard"><a class="url location" href="#">This web page</a> is copyright © 2017 by <a rel="me" href="/~patrick/" class="fn url">Patrick Mooney</a>. <abbr class="summary description" title="Last update to Patrick Mooney's explanation of the archive_junta.py script">Last update to this HTML file</abbr>: <abbr class="dtstart" title="%s">%s</abbr>. Short link to this page: <a rel="me" class="url" href="https://is.gd/fascist_archiver">https://is.gd/fascist_archiver</a>.</footer>

</div></body>
</html>
""" % (datetime.datetime.now().date().isoformat(), time.strftime('%d %b %Y'))
    with open(webpage_loc, mode="w") as the_html_file:
        the_html_file.write(the_page)