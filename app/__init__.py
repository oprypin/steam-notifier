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


__version__ = '0.2.6'

import sys
import os
import collections
import re

import qt; qt.init()
from qt.core import QRectF, QUrl, QTimer, QSize
from qt.gui import QImage, QPixmap, QIcon, QColor, QPainter, QFont, QDesktopServices, QCursor
from qt.widgets import QSystemTrayIcon, QMenu, QAction, QApplication, QMessageBox
from qt.util import qu, add_to



app = qu(QApplication, sys.argv, quit_on_last_window_closed=False)


from . import web, api


empty_images = {12: QPixmap('resources/empty_12.png'), 20: QPixmap('resources/empty_20.png')}


tray_icon = QSystemTrayIcon()

def make_action(text, **kwargs):
    return qu(QAction, text, tray_icon, **kwargs)


def about():
    import lxml
    import cssselect
    
    QMessageBox.information(None, "About", u"""
        <h1>Steam Notifier</h1>
        <h3>Version {}</h3>

        <p>(C) 2014-2015 Oleh Prypin &lt;<a href="mailto:blaxpirit@gmail.com">blaxpirit@gmail.com</a>&gt;</p>

        <p>License: <a href="http://www.gnu.org/licenses/gpl.txt">GNU General Public License Version 3</a></p>

        Using:
        <ul>
        <li>Python {}
        <li>Qt {}, {} {}
        <li>lxml {} (cssselect {})
        </ul>
    """.format(
        __version__,
        sys.version.split(' ', 1)[0],
        qt.version_str,
        qt.module, qt.module_version_str,
        lxml.etree.__version__, cssselect.__version__
    ))

def information():
    with open('README.md') as f:
        s = f.read()
    s = s.split('\n\n\n')[2].split('\n\n', 1)[1]
    s = re.sub(r'<(.+?)>', r'<a href="\1">\1</a>', s)
    s = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
    s = s.replace('\n\n', '<p>')
    QMessageBox.information(None, "Information", "<p>Welcome to <i>Steam Notifier</i>.<p>"+s)


def logout():
    for fn in ['settings/cookies.txt', 'settings/user.txt']:
        try:
            os.remove(fn)
        except OSError:
            pass
    quit()

def quit():
    tray_icon.hide()
    app.quit()


options_menu = add_to(QMenu("&Options"),
    make_action("&Check now", triggered=web.update),
    None,
    make_action("&Help...", triggered=information),
    make_action("&About...", triggered=about),
    None,
    make_action("&Log out and quit", triggered=logout),
    make_action("&Quit", triggered=quit),
)


tray_menu = add_to(QMenu(), options_menu)




categories = comments = None

icon_font = QFont('Helvetica [Arial]', weight=QFont.Bold)

def generate_icon(size, n):
    w, h = size.width(), size.height()

    img = QImage(size, QImage.Format_ARGB32_Premultiplied)
    img.fill(qt.transparent)
    
    g = QPainter(img)
    
    d = 0 if qt.major <= 4 else 0.5
    
    if n:
        g.fillRect(0, 0, w, h, QColor(92, 126, 16))

        sz = h*0.88 if n < 10 else w*0.7
        icon_font.setPixelSize(sz)
        
        g.setFont(icon_font)
        g.setPen(qt.white)
        g.drawText(QRectF(1, 1, w-1, h-1+sz*0.0025-d), qt.AlignCenter|qt.AlignVCenter, str(n))
    else:
        (_, empty) = max((k, v) for k, v in empty_images.items() if k <= min(w, h))

        g.drawPixmap(int(w/2-empty.width()/2), int(h/2-empty.height()/2), empty)
    
    del g
    
    return QIcon(QPixmap.fromImage(img))

last_n = None

def update_icon(categories, comments):
    global last_n
    n = sum(category.count for category in categories.values())
    if n != last_n:
        size = tray_icon.geometry().size()
        if not (size.width() and size.height()):
            size = QSize(22, 22)
        icon = generate_icon(size, n)
        tray_icon.setIcon(icon)
        last_n = n



def category_click(category):
    open_url(category.url)
    QTimer.singleShot(8000, web.update)

def comment_click(comment):
    open_url(comment.url)
    comments.remove(comment)
    categories.comments.count -= 1
    update()
    QTimer.singleShot(5000, web.update)


def group_comments(comments):
    groups = collections.OrderedDict({'': {}})
    for comment in comments:
        gr = comment.get('group') or ''
        if gr not in groups:
            groups[gr] = []
        groups[gr].append(comment)
    return groups


def update_menu(categories, comments):
    tray_menu.clear()
    
    for kind, category in categories.items():
        if not category.count:
            continue
        add_to(tray_menu, make_action(category.text,
            triggered=lambda category=category: category_click(category))
        )
        if kind == 'comments':
            for group, gr_comments in group_comments(comments).items():
                if group:
                    add_to(tray_menu, make_action('    {}:'.format(group),
                        triggered=lambda category=category: category_click(category))
                    )
                for comment in gr_comments:
                    add_to(tray_menu, make_action(u'        \u2022 {}'.format(comment.text),
                        triggered=lambda comment=comment: comment_click(comment), tool_tip=comment.tooltip)
                    )
            add_to(tray_menu, None)
    
    if not tray_menu.isEmpty():
        add_to(tray_menu, None)
        add_to(tray_menu, options_menu)
        qu(tray_icon, context_menu=tray_menu)
    else:
        qu(tray_icon, context_menu=options_menu)

def notify(categories, comments):
    msg = []
    total_categories = 0
    for kind, category in categories.items():
        if not category.count:
            continue
        total_categories += 1
        msg.append(category.text)
        if kind == 'comments':
            for group, gr_comments in group_comments(comments).items():
                if group:
                    msg.append('    {}:'.format(group))
                for comment in gr_comments:
                    msg.append(u'        \u2022 {}'.format(comment.text))
    if total_categories == 1:
        title, msg = msg[0], msg[1:]
    else:
        title = "Steam Notifier"
    tray_icon.showMessage(title, '\n'.join(msg), QSystemTrayIcon.NoIcon,
        round(api.config.notification_timeout*1000)
    )

def open_url(url, browser=api.config.open_urls_in):
    if browser in [None, 'default']:
        QDesktopServices.openUrl(QUrl(url))
    else:
        import webbrowser
        try:
            browser = webbrowser.get(browser)
        except webbrowser.Error:
            import subprocess
            subprocess.call([browser, url])
        else:
            browser.open_new_tab(url)


def update():
    update_icon(categories, comments)
    update_menu(categories, comments)

def process_data(data):
    global categories, comments
    categories, comments = data
    for comment in comments:
        title = comment.title
        if len(title) > 50:
            title = title[:50].strip()+'...'
        comment.text = (u'{} ({})' if comment.newposts > 1 else u'{}').format(title, comment.newposts)
        comment.tooltip = u'{}\n({})'.format(comment.description, comment.date)
    api.transform(categories, comments, notify)
    update()


def activate(reason=None):
    if reason == QSystemTrayIcon.DoubleClick or reason is None:
        if len(comments) == 1:
            comment_click(comments[0])
            return
        for category in categories.values():
            if category.count:
                category_click(category)
                return
        open_url('http://steamcommunity.com/my/commentnotifications')

qu(tray_icon, context_menu=options_menu, icon=QIcon(empty_images[20]), activated=activate, message_clicked=activate)

tray_icon.show()



try:
    with open('settings/user.txt') as f:
        pass
except IOError:
    about()
    information()

web.run(process_data)


app.exec_()