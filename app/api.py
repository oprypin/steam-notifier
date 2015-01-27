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
import collections

from . import web


def show_exception():
    from traceback import format_exc
    from qt.widgets import QMessageBox
    
    lines = format_exc().replace('  ', '    ').splitlines()
    try:
        index = next(i for i in range(len(lines)) if '"settings/config.py"' in lines[i])
        lines = lines[index:]
    except StopIteration: pass
    QMessageBox.critical(None, "Steam Notifier", "Error traceback:\n"+'\n'.join(lines))


try:
    config = imp.load_source('config', 'settings/config.py')
except Exception as e:
    show_exception()
    raise


web.timer.setInterval(round(config.interval*1000))


comments_notified = set()
categories_notified = {}


def transform(categories, comments, notify_f):
    for kind, category in categories.items():
        if not category.count:
            continue
        
        def ignore(category=category):
            category.to_ignore = True
        def notify(category=category, kind=kind):
            n = categories_notified.get(kind, 0)
            if category.count != n:
                if category.count > n:
                    category.to_notify = True
                categories_notified[kind] = category.count
        object.__setattr__(category, 'ignore', ignore)
        object.__setattr__(category, 'notify', notify)
        
        if kind == 'comments':
            for comment in comments:
                def ignore(comment=comment):
                    comment.to_ignore = True
                def mark_read(comment=comment):
                    ignore()
                    web.request(comment.get('read_url', comment.url))
                def notify(comment=comment, category=category):
                    if comment.url not in comments_notified:
                        category.to_notify = True
                        comment.to_notify = True
                        comments_notified.add(comment.url)

                object.__setattr__(comment, 'ignore', ignore)
                object.__setattr__(comment, 'mark_read', mark_read)
                object.__setattr__(comment, 'notify', notify)

            args = (category, comments)
        else:
            args = (category)
        
        try:
            f = getattr(config, kind)
            f(*args)
        except Exception as e:
            show_exception()
            raise
    
    notify_categories = collections.OrderedDict(
        (kind, category) for (kind, category) in categories.items() if category.get('to_notify')
    )
    if notify_categories:
        notify_f(notify_categories, [comment for comment in comments if comment.get('to_notify')])
    
    for kind, category in list(categories.items()):
        if category.get('to_ignore'):
            del categories[kind]
    for comment in list(comments):
        if comment.get('to_ignore'):
            comments.remove(comment)
    categories['comments'].count = len(comments)