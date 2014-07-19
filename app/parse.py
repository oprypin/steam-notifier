# Copyright (C) 2014 Oleh Prypin <blaxpirit@gmail.com>
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

import lxml.html
import cssselect


def parse_commentnotifications(content):
    root = lxml.html.fromstring(content)

    counts = AttributeOrderedDict()
    dropdown, = root.cssselect('#header_notification_dropdown')
    for cls in 'comments items invites gifts offlinemessages tradeoffers'.split():
        d = AttributeDict(count=0, kind=cls)
        counts[cls] = d
        try:
            el, = dropdown.cssselect('.header_notification_{}'.format(cls))
        except ValueError:
            continue
        d['text'] = el.text_content().strip()
        d['count'] = int(d['text'].split()[0])
        d['link'] = el.get('href')
    if not counts['offlinemessages']['link'].startswith('http://'):
        counts['offlinemessages']['link'] = 'http://steamcommunity.com/chat'

    comments = []
    block, = root.cssselect('#profileBlock')
    for notification in block.cssselect('.commentnotification.unread'):
        d = AttributeDict()
        for cls in 'newposts date title description'.split():
            el, = notification.cssselect('.commentnotification_{}'.format(cls))
            d[cls] = el.text_content().strip()
        d['newposts'] = int(d['newposts'].lstrip('+'))
        a, = notification.cssselect('a')
        d['link'] = a.get('href')
        comments.append(d)
    
    return counts, comments


class AttributeMixin:
    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattr__(self, name)
        return self[name]

class AttributeDict(dict, AttributeMixin):
    pass

class AttributeOrderedDict(collections.OrderedDict, AttributeMixin):
    pass