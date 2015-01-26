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


__version__ = '0.2.1'

import sys
import os
import collections

import qt; qt.init()
from qt.core import QRectF, QSize, QUrl, QTimer
from qt.gui import QImage, QPixmap, QIcon, QColor, QPainter, QLinearGradient, QFont, QDesktopServices, QCursor
from qt.widgets import QSystemTrayIcon, QMenu, QMainWindow, QAction, QApplication, QMessageBox
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
    
    QMessageBox.information(None, "About", """
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
    QMessageBox.information(None, "Information", """
        <p>
        Welcome to <i>Steam Notifier</i>.
        <p>
        This program works by simulating a web browser and downloading <a href="http://steamcommunity.com/my/commentnotifications">http://steamcommunity.com/my/commentnotifications</a> every 30 seconds. The page is then parsed to get the information about new comments you got in Steam Community as well as other events.
        <p>
        In order to do this, <i>Steam Notifier</i> will need you to login to Steam Community in the browser window that will be shown to you. Of course, entering your password in some suspicious looking window can be a risk. But this program does not store your login data in any way. And you don't have to just believe these words. The program's source code is available in its entirety.
        <p>
        The initial setup ends successfully when you reach your comment notifications page, and if everything goes well, you should be redirected there automatically after you log in. You may need to log in again from time to time if the session expires.
        <p>
        Afterwards, <i>Steam Notifier</i> will consist only of the system tray (notification area) icon with the number of new events (if any) on it, very similarly to the one you get inside Steam's main window. Right-clicking it will give you a menu with some self-explanatory options (including <i>Quit</i>), and also individual event groups. Clicking on the events in the menu will open the corresponding part of Steam Community website in your default browser. Double clicking the icon will select the first available event from that menu and send you to it.
        <p>
        Make sure to check out <i>settings/config.py</i> to configure filtering, notification popups and much more.
    """)


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


def activated(reason=None):
    if reason == QSystemTrayIcon.DoubleClick:
        activate()
    elif reason == None:
    #elif reason in [QSystemTrayIcon.Context, QSystemTrayIcon.Trigger]:
        tray_menu.popup(QCursor.pos())

qu(tray_icon, context_menu=options_menu, icon=QIcon(empty_images[12]), activated=activated, message_clicked=activated)

tray_icon.show()



categories = comments = None

icon_font = QFont('Helvetica [Arial]', weight=QFont.Bold)

def generate_icon(size, n):
    img = QImage(size, QImage.Format_ARGB32_Premultiplied)
    img.fill(qt.transparent)
    
    w, h = size.width(), size.height()
    
    (_, empty) = max((k, v) for k, v in empty_images.items() if k <= min(w, h))
    
    g = QPainter(img)
    
    if n:
        g.fillRect(0, 0, w, h, QColor(92, 126, 16))
    
    #g.setPen(QColor(92, 126, 16))
    d = 0 if qt.major <= 4 else 0.5
    #g.drawRoundedRect(QRectF(d, d, w-1, h-1), 3, 3)
    
    if n:
        sz = h*0.88 if len(str(n)) == 1 else w*0.7
        icon_font.setPixelSize(sz)
        
        g.setFont(icon_font)
        g.setPen(qt.white)
        g.drawText(QRectF(1, 1, w-1, h-1+sz*0.0025-d), qt.AlignCenter|qt.AlignVCenter, str(n))
    else:
        g.drawPixmap(int(w/2-empty.width()/2), int(h/2-empty.height()/2), empty)
    
    del g
    
    return QIcon(QPixmap.fromImage(img))

def update_icon(categories, comments):
    n = sum(category.count for category in categories.values())
    icon = generate_icon(tray_icon.geometry().size(), n)
    tray_icon.setIcon(icon)



def category_click(category):
    open_url(category.url)

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
          triggered=lambda category=category: category_click(category)))
        if kind == 'comments':
            for group, gr_comments in group_comments(comments).items():
                if group:
                    add_to(tray_menu, make_action('    {}:'.format(group),
                      triggered=lambda category=category: category_click(category)))
                for comment in gr_comments:
                    add_to(tray_menu, make_action(u'        \u2022 {}'.format(comment.text),
                      triggered=lambda comment=comment: comment_click(comment), tool_tip=comment.tooltip))
            add_to(tray_menu, None)
    
    if not tray_menu.isEmpty():
        add_to(tray_menu, None)
        add_to(tray_menu, options_menu)
        qu(tray_icon, context_menu=tray_menu)
    else:
        qu(tray_icon, context_menu=options_menu)

def notify():
    msg = []
    for kind, category in categories.items():
        if not category.count or not category.get('notify'):
            continue
        msg.append(category.text)
        if kind == 'comments':
            for group, gr_comments in group_comments(comments).items():
                if group:
                    msg.append('    {}:'.format(group))
                for comment in gr_comments:
                    msg.append(u'        \u2022 {}'.format(comment.text))
    tray_icon.showMessage("Steam Notifier", '\n'.join(msg), QSystemTrayIcon.NoIcon, round(api.config.notification_timeout*1000))

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


def activate():
    for category in categories.values():
        if category.count:
            open_url(category.url)
            return
    open_url('http://steamcommunity.com/my/commentnotifications')

def update():
    update_icon(categories, comments)
    update_menu(categories, comments)

def process_data(data):
    global categories, comments
    categories, comments = data
    for c in comments:
        c.text = '{} ({})'.format(c.title, c.newposts)
        c.tooltip = '{}\n({})'.format(c.description, c.date)
    api.go(categories, comments, notify)
    update()

try:
    with open('settings/user.txt') as f:
        pass
except OSError:
    about()
    information()

web.run(process_data)


app.exec_()