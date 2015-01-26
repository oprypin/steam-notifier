import re


interval = 30.0  # Check every N seconds

notification_timeout = 5.0  # Notifications should disappear in N seconds

open_urls_in = 'default'  # Your system's default browser
             # 'firefox'  # Some predefined value
                          # https://docs.python.org/3/library/webbrowser.html#webbrowser.register
             # r'/usr/bin/firefox'  # Path to any executable

# See documentation below

def comments(info, comments):
    # Uncomment to see the data structures for yourself:
    # with open('comments.txt') as f:
    #    f.write(str(comments))
    
    for comment in comments:
        # show comments grouped by description
        comment.group = comment.description  # remove this line to disable grouping
        
        if comment.kind == 'deleted':
            comment.mark_read()  # ignore and mark as read the deleted items
        
        elif comment.kind == 'discussion':
            # avoid separation of new discussions and followups (different description)
            comment.group = comment.forum
            
            # use regular expressions to find unwanted discussions (mostly trading)
            # https://docs.python.org/3/library/re.html
            matches = re.findall(r'''
                \[H\] | \[W\]   # [H] or [W]
               |\b(H|W|coupon|trading|trade|card|cards|discount|offer|gems|key)\b   # whole words
               |\b([1-9][05]|33|66)%   # coupons
            ''', comment.title, re.IGNORECASE|re.VERBOSE)
            if len(matches) >= 2:    # if at least 2 matches,
                comment.mark_read()  # ignore and mark as read
            elif len(matches) == 1:  # if just 1 match,
                comment.ignore()     # don't show it in Steam Notifier, but leave it

        # notify about your own items or replies on others' profiles, statuses, new games
        elif comment.owner:
            comment.notify()
        elif comment.kind in ['profile', 'status', 'newgame']:
            comment.notify()


def items(info):
    pass  # "do nothing" (empty functions are not allowed)

def invites(info):
    pass

def gifts(info):
    info.notify()  # notify about gifts

def offlinemessages(info):
    info.notify()  # notify about private messages

def tradeoffers(info):
    pass


"""
info argument for every function has the following members:

- count: how many new notifications of that category
         int [19]
- text: text of that notification, will be shown in menu
        str ["19 new comments"]
- url: URL for more details, will be opened on activation
       str ['http://steamcommunity.com/id/blaxpirit/commentnotifications/']

- ignore(): don't show any notifications about this category in Steam Notifier, but leave it in Steam
- notify(): include this category in the popup notification

comments argument is a list of comments, each of which has the following members:

- kind: str - one of the following:
      - 'deleted'    - this item was moved or deleted
      - 'discussion' - in forum discussions
      - 'profile'    - on profile
      - 'status'     - on status post
      - 'newgame'    - on "now owns this game"
      - 'guide'      - on a guide
- newposts: how many new posts in that thread
            int [1]
- date: when it happened
        str ["9 hours ago"]
- title: 1st line of the notification (topic title)
         str ["I need help!"]
- description: 2nd line
               str ["A new discussion in Boson X General Discussions"]
- url: visit to view notification, will be opened on activation
       str ['http://steamcommunity.com/app/302610/discussions/0/613948093890273167/']
- owner: bool - one of the following:
       - True  - it's your own discussion/guide/newgame/profile/status
       - False - you got a reply on someone else's item
- subscribed: True usually means you got a followup reply on the forum
              bool
- new: (present only for 'discussion' kind) is it a new discussion or a followup
       bool
- forum: (present only for 'discussion' kind) forum name (part of the description)
         str ["Boson X General Discussions"]
- text: the text that will be shown in the menu of Steam Notifier
        str ["I need help! (1)"]
- tooltip: the tooltip on hover of the menu item (won't show on some systems), can be modified
           str ["A new discussion in Boson X General Discussions\n(9 hours ago)"]
- read_url: URL to visit to mark this item as read (mostly internal use)
            str ['http://steamcommunity.com/comment/ForumTopic/removenotification/.../...?feature2=...']
- group: set this value to group comments in the popup menu
         str []

- ignore(): don't show any notifications about this message in Steam Notifier, but leave it in Steam
- mark_read(): ignore and mark as read
- notify(): include this comment in the popup notification
"""