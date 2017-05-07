The Fascist Tweet-Archiving Script `archive_junta.py`
=====================================================

<a rel="me" href="http://patrickbrianmooney.nfshost.com/~patrick/">Patrick Mooney</a><br />
v 0.2: 22 February 2017

Overview
--------

This script runs on one of my spare laptops, constantly listening for new tweets on certain Twitter accounts and, when new tweets occur, using the Internet Archive to create an offsite copy of those tweets. It started out just watching Donald Trump's Twitter accounts, but starting from 22 February 2017, it also watches the Twitter accounts of other members of America's current corporatist junta.

If you have non-technical questions about this script, you should take a look at the (off-GitHub) <a rel="me" href="http://patrickbrianmooney.nfshost.com/~patrick/projects/FascistTweetArchiver/">project home page</a>. The document you're looking at right now just talks about the technical aspects of the process.

“How does it work?”
-------------------

The script runs as continuously as possible on a spare laptop in my apartment under Python 3 (and, more specifically, in my case it runs under Python 3.4.3 on a Dell Latitude D420 running Crunchbang++ based on Debian 8.7). The script sits there, using the [Twitter streaming API](https://dev.twitter.com/streaming/overview) to wait for notification that new tweets have come in from the accounts it's monitoring. Any time it gets that notification, it asks the Internet Archive to create a backup of the web page displaying the tweet.

To guard against the possibility that the running script quits for any reason, my laptop re-runs the script as a `cron` job once a minute. The first thing it does when it starts up is check to see if there's another copy running; if there is one, the newly started copy quits. So the `cron` job simply starts it over and over, and the new copy usually just quits more or less immediately. If there are no other copies of the script running when it starts up, it checks to see what ID of the last tweet it saw was from each account that it follows, then archives all of the tweets that have come in since the last time the script ran (if there are in fact any new tweets).

“What do I need to run this script?”
------------------------------------

-   Python 3.X
-   a more-or-less continuously available Internet connection
-   Several PyPI modules not in the standard library (which you can install using `pip` or `easy_install`, or put into a virtualenv):
    -   [Tweepy](http://www.tweepy.org)
    -   [`pid`](https://pypi.python.org/pypi/pid/)
    -   [Tumblpy](https://github.com/michaelhelmick/python-tumblpy)
-   A couple of modules from my personal library on GitHub (which you can just drop into the same folder from which you're running the main script):
    -   [`social_media.py`](https://github.com/patrick-brian-mooney/python-personal-library/blob/master/social_media.py)
    -   [`patrick_logger.py`](https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py)
-   A [Twitter API key](http://stackoverflow.com/questions/1808855/getting-new-twitter-api-consumer-and-secret-keys) for the script to use.

I run it under Linux, but there's no basic reason why it couldn't run under Windows or OS X.

“It's crashing with errors!”
----------------------------

Is it crashing with `AttributeError: 'NoneType' object has no attribute 'strip'`? If your installed version of Tweepy (try `pip3 show tweepy` or `pip show tweepy`) is 3.5, try installing another version. As of the time of this writing, the best option seems to be manually cloning the Tweepy repository on GitHub and using that to install Tweepy 3.6. (See the [installation instructions](https://github.com/tweepy/tweepy). Though various places around the web sometimes suggest Tweepy 3.2 for other versions of this problem, it does not work well with `archive_junta.py`. You've been warned.)

If you're having trouble running the script in a Debian-based Linux distribution (and perhaps others?), and especially if you're getting errors claiming that `IncompleteRead` and/or `ProtocolError` are undefined names, you might try [updating your copy of `pip` or `pip3`](http://stackoverflow.com/questions/27341064/how-do-i-fix-importerror-cannot-import-name-incompleteread).

“Can I adapt it to archive tweets from other accounts in the same way?”
---------------------------------------------------------

Sure, and don't feel obligated to tell me that you're doing so (though you can if you want to!). You can fork it [on GitHub](https://github.com/patrick-brian-mooney/archive-trump), or just download it and play with it yourself. It's offered under the GPL license, either version 3 or (at your choice) any later version. See the file [LICENSE.md](https://github.com/patrick-brian-mooney/archive-trump/blob/master/LICENSE.md) for details.
