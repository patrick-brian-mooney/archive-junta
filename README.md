The Fascist Tweet-Archiving Script `archive_trump.py`
=====================================================

<a rel="me" href="http://patrickbrianmooney.nfshost.com/~patrick/">Patrick Mooney</a><br />
v 0.2: 22 February 2017

Overview
--------

This script runs on one of my spare laptops, constantly listening for new tweets on certain Twitter accounts and, when new tweets occur, using the Internet Archive to create an offsite copy of those tweets. It started out just watching Donald Trump's Twitter accounts, but as of 22 February 2017, it also watches the Twitter accounts of Mike Pence.

If you have non-technical questions about this script, you should take a look at the (off-GitHub) <a rel="me" href="">project home page</a>. This 

“How does it work?”
-------------------

The script runs under Linux (more specifically, on a Dell Latitude D420 running Crunchbang++ based on Debian 8.7) as continuously as possible on a spare laptop in my apartment. The script sits there, using the [Twitter streaming APIs](https://dev.twitter.com/streaming/overview) to wait for notification that new tweets have come in from the accounts it's watching. (“Watching” is perhaps a inadequately specific without additional clarification here: the script is listening, but doesn't create any follower-followee relationships between Twitter accounts. No, I don't have to follow Trump or Pence to get the script running. Think “watching” in terms of “watching TV,” not “watching” as in “following on Twitter.”) Any time it gets that notification, it asks the Internet Archive to create a backup of the web page displaying the tweet.

To guard against the possibility that the running script quits for any reason, my laptop re-runs the script as a `cron` job once a minute. The first thing it does when it starts up is check to see if there's another copy running; if there is one, the newly started copy quits, so the `cron` job simply starts it over and over, and the new copy usually just quits more or less immediately. If there are no other copies of the script running when it starts up, it checks to see what ID of the last tweet it saw was from each account that it follows, then archives all of the tweets that have come in since the last time the script ran (if there are in fact any new tweets).

“What do I need to run this script?”
------------------------------------

-   Python 3.X
-   a more-or-less continuously available Internet connection
-   Several PyPI modules not in the standard library:
    -   [Tweepy](http://www.tweepy.org)
    -   [`pid`](https://pypi.python.org/pypi/pid/)
    -   [Tumblpy](https://github.com/michaelhelmick/python-tumblpy)
-   A couple of modules from my personal library on GitHub (which you can just drop into the same folder from which you're running the main script):
    -   `social_media.py`
    -   [`patrick_logger.py`](https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py)
-   A [Twitter API key](http://stackoverflow.com/questions/1808855/getting-new-twitter-api-consumer-and-secret-keys) for the script to use.

I run it under Linux, but there's no basic reason why it couldn't run under Windows or OS X. If you're having trouble running the script in a Debian-based Linux distribution (and perhaps others?), and especially if you're getting errors claiming that `IncompleteRead` and/or `ProtocolError` are undefined names, you might try [updating your copy of `pip` or `pip3`](http://stackoverflow.com/questions/27341064/how-do-i-fix-importerror-cannot-import-name-incompleteread).

“Can I adapt it to archive other people in the same way?”
---------------------------------------------------------

Sure, and don't feel obligated to tell me that you're doing so (though you can if you want to!). You can fork it [on GitHub](https://github.com/patrick-brian-mooney/archive-trump), or just download it and play with it yourself. It's offered under the GPL license, either version 3 or (at your choice) any later version. See the file [LICENSE.md](https://github.com/patrick-brian-mooney/archive-trump/blob/master/LICENSE.md) for details.
