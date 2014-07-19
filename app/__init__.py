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


import sys
import os

import qt; qt.init()
from qt.core import QRectF, QSize, QUrl, QTimer
from qt.gui import QImage, QPixmap, QIcon, QColor, QPainter, QLinearGradient, QFont, QDesktopServices, QCursor
from qt.widgets import QSystemTrayIcon, QMenu, QMainWindow, QAction, QApplication, QMessageBox
from qt.util import qu, add_to


try:
    os.mkdir('settings')
except OSError:
    pass

app = qu(QApplication, sys.argv, quit_on_last_window_closed=False)


from . import web



button_colors = (
    (QColor(92, 90, 87), QColor(38, 38, 37), QColor(50, 48, 47)),
    (QColor(92, 126, 16), QColor(92, 126, 16), QColor(52, 50, 47)),
)
letter_images = (QPixmap('resources/empty.png'), QPixmap('resources/full.png'))



def activated(reason):
    if reason==QSystemTrayIcon.DoubleClick:
        double_click()
    #elif reason in [QSystemTrayIcon.Context, QSystemTrayIcon.Trigger]:
        #tray_menu.popup(QCursor.pos())



tray_icon = QSystemTrayIcon()

def make_action(text, **kwargs):
    return qu(QAction, text, tray_icon, **kwargs)


def about():
    import lxml
    import cssselect
    
    QMessageBox.information(None, "About", """
        <h1>Steam Notifier</h1>
        <h3>Version 0.1</h3>

        <p>(C) 2014 Oleh Prypin &lt;<a href="mailto:blaxpirit@gmail.com">blaxpirit@gmail.com</a>&gt;</p>

        <p>License: <a href="http://www.gnu.org/licenses/gpl.txt">GNU General Public License Version 3</a></p>

        Using:
        <ul>
        <li>Python {}
        <li>Qt {}, {} {}
        <li>lxml {} (cssselect {})
        </ul>
    """.format(
        sys.version.split(' ', 1)[0],
        qt.version_str,
        qt.module, qt.module_version_str,
        lxml.etree.__version__, cssselect.__version__
    ))

def information():
    QMessageBox.information(None, "Information", """
        <p>Welcome to <i>Steam Notifier</i>.</p>
        
        <p>This program works by simulating a web browser and downloading <a href="http://steamcommunity.com/my/commentnotifications">http://steamcommunity.com/my/commentnotifications</a> every 30 seconds. The page is then parsed to get the information about new comments you got in Steam Community as well as other events.</p>
        
        <p>In order to do this, <i>Steam Notifier</i> will need you to login to Steam Community in the browser window that will be shown to you. Of course, entering your password in some suspicious looking window can be a risk. But this program does not store your login data in any way. And you don't have to just believe these words. The program's source code is available in its entirety.</p>
        
        <p>The initial setup ends successfully when you reach your comment notifications page, and if everything goes well, you should be redirected there automatically after you log in.</p>
        
        <p>Afterwards, <i>Steam Notifier</i> will consist only of the system tray (notification area) icon with the number of new events (if any) on it, very similarly to the one you get inside Steam's main window. Right-clicking it will give you a menu with some self-explanatory options (including <i>Quit</i>), and also individual event groups. Clicking on the events in the menu will open the corresponding part of Steam Community website in your default browser. Double clicking the icon will select the first available event from that menu and send you to it.</p>
        
        <p>You may need to log in again from time to time if the session expires.</p>
    """)


def logout():
    try:
        os.remove('settings/cookies.txt')
    except OSError:
        pass
    try:
        os.remove('settings/user.txt')
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


qu(tray_icon, context_menu=options_menu, icon=QIcon(letter_images[1]), activated=activated)

tray_icon.show()



counts = comments = None

icon_font = QFont('Helvetica [Arial]', weight=QFont.Bold)

def generate_icon(size, n):
    img = QImage(size, QImage.Format_ARGB32_Premultiplied)
    img.fill(qt.transparent)
    
    colors = button_colors[bool(n)]
    letter = letter_images[bool(n)]
    
    w, h = size.width(), size.height()
    
    g = QPainter(img)
    
    grad = QLinearGradient(0, 0, 0, h-2)
    grad.setColorAt(0, colors[1])
    grad.setColorAt(1, colors[2])
    g.fillRect(1, 1, w-2, w-2, grad)
    
    g.setPen(colors[0])
    d = 0 if qt.major<=4 else 0.5
    g.drawRoundedRect(QRectF(d, d, w-1, h-1), 3, 3)
    
    if n:
        sz = h*0.88 if len(str(n))==1 else w*0.7
        icon_font.setPixelSize(sz)
        
        g.setFont(icon_font)
        g.setPen(qt.white)
        g.drawText(QRectF(1, 1, w-1, h-1+sz*0.0025-d), qt.AlignCenter|qt.AlignVCenter, str(n))
    else:
        g.drawPixmap(int(w/2-letter.width()/2), int(h/2-letter.height()/2), letter)
    
    del g
    
    return QIcon(QPixmap.fromImage(img))

def update_icon(counts, comments):
    n = sum(item.count for item in counts.values())
    icon = generate_icon(tray_icon.geometry().size(), n)
    tray_icon.setIcon(icon)



def count_click(item):
    open_link(item.link)

def comment_click(item):
    open_link(item.link)
    comments.remove(item)
    counts['comments']['count'] -= 1
    update()
    QTimer.singleShot(5000, web.update)
    

def update_menu(counts, comments):
    tray_menu.clear()
    
    for item in counts.values():
        if not item.count:
            continue
        add_to(tray_menu, make_action(item.text, triggered=lambda item=item: count_click(item)))
        if item.kind=='comments':
            for item in comments:
                add_to(tray_menu, make_action(
                    u' \u2022 {} ({})'.format(item.title, item.newposts),
                    triggered=lambda item=item: comment_click(item),
                    tool_tip='{}\n({})'.format(item.description, item.date)
                ))
            add_to(tray_menu, None)
    
    if tray_menu.isEmpty():
        add_to(tray_menu, make_action("No new events", disabled=True))
    add_to(tray_menu, None)
    add_to(tray_menu, options_menu)
    
    qu(tray_icon, context_menu=tray_menu)

def open_link(url):
    QDesktopServices.openUrl(QUrl(url))

def double_click():
    for item in counts.values():
        if item.count:
            open_link(item.link)
            break

def update():
    update_icon(counts, comments)
    update_menu(counts, comments)

def process_data(data):
    global counts, comments
    counts, comments = data
    print(counts)
    print(comments)
    update()

try:
    with open('settings/user.txt') as f:
        pass
except OSError:
    about()
    information()


web.run(process_data)


app.exec_()