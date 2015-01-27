# Copyright (C) 2014-2015 Oleh Prypin <blaxpirit@gmail.com>
# 
# This file is part of Steam Notifier.
# 
# Steam Notifier is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Steam Notifier is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Steam Notifier.  If not, see <http://www.gnu.org/licenses/>.


import collections
import re
import json

import lxml.html
import cssselect


def parse_commentnotifications(content):
    root = lxml.html.fromstring(content)

    categories = AttributeDict()
    [dropdown] = root.cssselect('#header_notification_dropdown')
    for cls in 'comments items invites gifts offlinemessages tradeoffers'.split():
        category = AttributeDict(count=0)
        categories[cls] = category
        try:
            [el] = dropdown.cssselect('.header_notification_{}'.format(cls))
        except ValueError:
            continue
        category.text = el.text_content().strip()
        category.count = int(category.text.split()[0])
        category.url = el.get('href')
    if not categories.offlinemessages.url.startswith('http'):
        categories.offlinemessages.url = 'https://steamcommunity.com/chat/'
    if not categories.tradeoffers.get('url'):
        categories.tradeoffers.url = 'http://steamcommunity.com/my/tradeoffers/'

    comments = []

    [comment_info] = re.findall(b'''InitCommentNotifications\( *(\[.*?\]),''', content)
    comment_info = json.loads(comment_info.decode('utf-8'))
    
    [block] = root.cssselect('#profileBlock')
    for notification, info in zip(block.cssselect('.commentnotification'), comment_info):
        comment = AttributeDict()

        kind = info['type'].lower().strip('_')
        comment.kind = {'forumtopic': 'discussion', 'userreceivednewgame': 'newgame', 'userstatuspublished': 'status'}.get(kind, kind)

        for cls in 'newposts date title description'.split():
            [el] = notification.cssselect('.commentnotification_{}'.format(cls))
            comment[cls] = el.text_content().strip()

        if 'unread' not in notification.get('class').split():
            continue
        
        comment.newposts = int(comment.newposts.lstrip('+') or 0)

        [a] = notification.cssselect('a')
        comment.url = a.get('href').rstrip('#')
        
        comment.owner = bool(info['is_owner'])
        comment.subscribed = bool(info['is_subscribed'])


        if comment.kind == 'deleted':
            m = re.match(r'''^RemoveCommentNotification\( *this, *'(.+?)', *'(.+?)', *'(.+?)'(?:, *'(.+?)' *)?\);?$''', notification.get('onclick'))
            url = 'http://steamcommunity.com/comment/{}/removenotification/{}/{}'
            if m.group(4):
                url += '?feature2={}'

            [sessionid] = re.findall(b'''g_sessionID *= *["'](.+?)["']''', content)
            comment.read_url = (url.format(*m.groups()), b'sessionid='+sessionid)
        
        if comment.kind == 'discussion':
            m = re.match(r'^A (new) discussion in (.+)$', comment.description) or re.match(r'^()In (.+)$', comment.description)
            comment.new = bool(m.group(1))
            comment.forum = m.group(2)
        #if comment.description == "Your profile":
            #comment.kind = 'profile'
        #if '/friendactivitydetail/' in comment.url or '/status/' in comment.url:
            #comment.kind = 'friendactivity'
        #if '/sharedfiles/' in comment.url:
            #comment.kind = 'content'

        comments.append(comment)
    
    return categories, comments




class AttributeDict(collections.OrderedDict):
    def __getattr__(self, name):
        if name.startswith('_'):
            return collections.OrderedDict.__getattr__(self, name)
        return self[name]
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            return object.__setattr__(self, name, value)
        self[name] = value
    
    def __repr__(self):
        result = []
        for k, v in self.items():
            v = ('\n   '+' '*len(k)).join(repr(v).strip().splitlines())
            result.append('{}: {}'.format(k, v))
        return '\n{'+',\n '.join(result)+'}'