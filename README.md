`archive_trump.py`
==================

<a rel="me" href="http://patrickbrianmooney.nfshost.com/~patrick/">Patrick Mooney</a><br />
v 0.2: 22 February 2017

Overview
--------

This script runs on one of my spare laptops, constantly listening for new tweets on certain Twitter accounts and, when new tweets occur, using the Internet Archive to create an offsite copy of those tweets. It started out just following Donald Trump's Twitter accounts, but as of 22 February 2017, it also follows the Twitter accounts of Mike Pence.

The full list of accounts currently archived by my use of this script is:

* @POTUS (archive <a href="http://web.archive.org/web/*/https://twitter.com/POTUS/*">here</a>)
* @realDonaldTrump (archive <a href="http://web.archive.org/web/*/https://twitter.com/realDonaldTrump/*">here</a>)
* @VP (archive <a href="http://web.archive.org/web/*/https://twitter.com/VP/*">here</a>)
* @mike_pence (archive <a href="http://web.archive.org/web/*/https://twitter.com/mike_pence/*">here</a>)
* @GovPenceIN (archive <a href="http://web.archive.org/web/*/https://twitter.com/GovPenceIN/*">here</a>)
 
My intent is to get a neutral third party to create backups of the tweets before they can be deleted, because a neutral third-party archive is a more credible source than a screenshot that I produced on my own computer and totally swear I didn't alter. (It's also easier to produce automatically.)

Why would you do this in the first place?
-----------------------------------------

Because words matter, especially the words spoken by elected officials; they have wide-ranging effects even after their material presence has evaporated into the ether. That is to say that Donnie's profound contempt for facts and his repeated insistence on inventing them are both troubling, and I suspect that there's a connection with the surprisingly frequent deletion of his own posts on Twitter.

When The Donald deletes a tweet, that doesn't mean that the deleted words have had no effect; they still influence the thoughts and behavior of (at least some of) his supporters. All it really means is that the effect is harder to trace back to the newly absent cause. My thought is that producing an archive at an external source helps to reinforce, in a small way, the underlying discursive structures upon which a functioning democracy depends.

Should I run a copy of this script?
-----------------------------------

Maybe! I myself am just running the script on a spare laptop in my apartment, and that's not a perfect setup: my electricity or Internet service could go out, or the laptop could overheat, or its old hardware might be running the script too slowly to catch a tweet before it's erased, or any number of other things could go wrong. Having several people&mdash;certainly even a dozen or so would be overkill&mdash;all running this script (or taking similar actions) would provide a level of redundancy that would help to make always capturing every tweet at least once much more likely.

On the other hand, if *way too many people* decide to volunteer in this way, that would unnecessarily burden the infrastructures of both the Internet Archive and Twitter for little to no practical benefit. So my proposal is this: if you plan to run another copy of this script, let me know (hit me up <a rel="me" href="https://twitter.com/patrick_mooney">on Twitter</a>, and I'll keep an up-to-date count (and/or tally) here.

To the best of my knowledge, there are currently **no other people** running this script remotely.

Is your script ensuring there is a complete archive of all of Trump's (and Pence's) tweets?
-------------------------------------------------------------------------------------------
No. There are at least two groups of tweets that the script is not archiving:

1. **Very old tweets.** The Twitter API only allows access to someone's last 3200 or so tweets, so the first tweet this script archived was probably produced by Donnie somewhere around March 2016. I have not made any attempt to go back and algorithmically save older Trump tweets, in part because that would require a totally different methodology, and quite possibly substantial manual intervention. (There *are* older Trump tweets archived on the Internet Archive, but they were not saved by me.)
2. **Tweets that both appear and disappear while the script is not running.** If the power goes off in my apartment, or if the script crashes, and Donnie tweets and then deletes that tweet before the script runs again, then the tweet won't get archived. Similarly, it is possible that a tweet could get noticed but still disappear before it can be archived.

There are at least two other groups of potential problems that might, in theory, keep a tweet from being archived:

1. The Twitter API could, in theory, not report that a tweet was posted, or could do so with a large enough delay to allow him or his goony henchmen to delete it before it could be archived.
2. It is possible, in theory, that Creepy Don or his servile brigade might interfere with one or more of the services required for this to work.

I don't currently have cause to believe that anything has been missed for any of the reasons above except for "very old tweets" ... but then, if it did, how would I know? (This is part of why it would be good if several other people were also running this script.) 

Were all of the Trump/Pence tweets on the Internet Archive saved by your script?
--------------------------------------------------------------------------------
No. Anyone can save a web page to the Internet Archive (IA) at any time, and I am certainly not the only person who has decided to have the IA save copies of Trump's tweets. (Though, to the best of my knowledge, I am the first to think that doing so systematically is a good idea.) 

How does it work?
-----------------

The script runs as continually as possible on a spare laptop running Linux (more specifically, on a Dell Latitude D420 running Crunchbang++ based on Debian 8.7). It sits there, using the Twitter streaming API to wait for notification that new tweets have come in from the accounts it's watching. ("Watching" is perhaps a inadequately specific without additional clarification here: the script is listening, but doesn't create any follower-followee relationships between Twitter accounts. No, I don't have to follow Trump or Pence to get the script running. Think "watching" in terms of "watching TV," not "watching" as in "following on Twitter.")  Any time it gets that notification, it asks the Internet Archive to create a backup of the web page displaying the tweet. 

To guard against the possibility that the running script quits for any reason, my laptop re-runs the script as a `cron` job once a minute. The first thing it does when it starts up is check to see if there's another copy running and, if so, quits, so the `cron` job simply starts it over and over, and the new copy usually just quits more or less immediately. If there are no other copies of the script running when it starts up, it checks to see what ID of the last tweet it saw was from each account that it follows, then archives all of the tweets that have come in since the last time the script ran (if there are in fact any new tweets).

What do I need to run this script?
----------------------------------

<ul>
<li>Python 3.X</li>
<li>a more-or-less continuously available Internet connection</li>
<li>Several PyPI modules not in the standard library:
    <ul>
        <li><a rel="muse" href="http://www.tweepy.org">Tweepy</a></li>
        <li><a rel="muse" href="https://pypi.python.org/pypi/pid/"><code>pid</code></a></li>
        <li><a rel="muse" href="https://github.com/michaelhelmick/python-tumblpy">Tumblpy</a></li>
    </ul>
</li>
<li>A couple of modules from my personal library on GitHub (which you can just drop into the same folder from which you're running the main script):
    <ul>
        <li><a rel="me" href="https://github.com/patrick-brian-mooney/python-personal-library/blob/master/social_media.py"><code>social_media.py</code></a></li>
        <li><a rel="me" href="https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py"><code>patrick_logger.py</code></a></li>
    </ul>
</li>
</ul>

If you're having trouble running the script in a Debian-based Linux distribution (and perhaps others?), and especially if you're getting errors claiming that `IncompleteRead` and/or `ProtocolError` are undefined names, you might try <a rel="muse" href="http://stackoverflow.com/questions/27341064/how-do-i-fix-importerror-cannot-import-name-incompleteread">updating your copy of `pip` or `pip3`</a>.


Can I adapt it to follow other people in the same way?
------------------------------------------------------

Sure, and don't feel obligated to tell me that you're doing so (though you can if you want!). You can fork it <a href="https://github.com/patrick-brian-mooney/archive-trump">on GitHub</a>, or just download it and play with it yourself. It's offered under the GPL license, either version 3 or (at your choice) any later version. See the file [LICENSE.md](https://github.com/patrick-brian-mooney/archive-trump/blob/master/LICENSE.md) for details.
