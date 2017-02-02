`archive_trump.py`
========================

<a rel="me" href="http://patrickbrianmooney.nfshost.com/~patrick/">Patrick Mooney</a>
v 0.1: 1 February 2017

Overview
--------

This script runs on a spare laptop of mine, constantly listening for new tweets on certain Twitter accounts and, when new tweets occur, uses the Internet Archive to create a copy of those tweets. The accounts currently followed by my use of this script are @POTUS and @realDonaldTrump, and my intent is to get a neutral third party to create backups of the tweets before they can be deleted.

Why would you do that?
----------------------

I guess that depends on why you think Donald Trump sometimes deletes his tweets.

Should I run a copy of this script?
-----------------------------------

Maybe. I'm just running the script on a spare laptop in my apartment, and that's not a perfect setup: my electricity or Internet service could go out, or the laptop could overheat, or the old hardware might be running the script too slowly to catch a tweet before it's erased, or any number of other things could go wrong. Having several people &mdash; certainly no more than a dozen or so &mdash; all running this script (or taking similar actions) would provide a level of redundancy that would help to make always capturing every tweet at least once much more likely.

On the other hand, if *way too many people* decide to volunteer in this way, that would unnecessarily burden the infrastructures of both the Internet Archive and Twitter for little to no practical benefit. So my proposal is this: if you plan to run another copy of this script, let me know, and I'll keep an up-to-date count (and/or tally) here.

To the best of my knowledge, there are currently no other people running this script remotely.

Can I adapt it to follow other people in the same way?
------------------------------------------------------

Sure, and don't feel obligated to tell me that you're doing so. You can fork it <a href="https://github.com/patrick-brian-mooney/archive-trump">on GitHub</a>, or just download it and play with it yourself. It's offered under the GPL license, either version 3 or (at your choice) any later version. See the file [LICENSE.md]() for details.

How does it work?
-----------------

Etc.