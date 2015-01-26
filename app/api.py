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


import imp

from . import web


config = imp.load_source('config', 'settings/config.py')

web.timer.setInterval(round(config.interval*1000))


notified_comments = set()
categories_notified = {}


def go(categories, comments, notify_f):
    global should_notify
    should_notify = False
    
    for kind, category in categories.items():
        if not category.count:
            continue
        
        def ignore(category=category):
            category.ignored = True
        def notify(category=category):
            n = categories_notified.get(kind, 0)
            if category.count != n:
                if category.count > n:
                    global should_notify
                    should_notify = True
                    category.notify = True
                categories_notified[kind] = category.count
        object.__setattr__(category, 'ignore', ignore)
        object.__setattr__(category, 'notify', notify)

        
        try:
            f = getattr(config, kind)
        except AttributeError:
            config.other(kind, category)
        else:
            if kind == 'comments':
                for comment in comments:
                    def ignore(comment=comment):
                        comment.ignored = True
                    def mark_read(comment=comment):
                        ignore()
                        web.request(comment.get('read_url', comment.url))
                    def notify(comment=comment, category=category):
                        if comment.url not in notified_comments:
                            global should_notify
                            should_notify = True
                            category.notify = True
                            comment.notify = True
                            notified_comments.add(comment.url)

                    object.__setattr__(comment, 'ignore', ignore)
                    object.__setattr__(comment, 'mark_read', mark_read)
                    object.__setattr__(comment, 'notify', notify)

                f(category, comments)
            else:
                f(category)
    
    for kind, category in list(categories.items()):
        if category.get('ignored'):
            del categories[kind]
    for comment in list(comments):
        if comment.get('ignored'):
            comments.remove(comment)
    categories['comments'].count = len(comments)
    
    if should_notify:
        notify_f()