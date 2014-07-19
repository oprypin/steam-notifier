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


import qt
from qt.network import QNetworkAccessManager, QNetworkRequest
from qt.webkit import QWebPage, QWebView
from qt.core import QTimer, QUrl

from qt.util import qu

from .cookies import PersistentCookieJar
from .parse import parse_commentnotifications


cookie_jar = PersistentCookieJar('settings/cookies.txt')
nam = qu(QNetworkAccessManager, cookie_jar=cookie_jar)

def found_login_url(url):
    if not url.path().startswith('/login'):
        return False
    
    global page, view
    page = qu(QWebPage, network_access_manager=nam)

    def load_progress(progress):
        qu(view, window_title=page.mainFrame().url().toString())

    def load_finished(ok):
        global page, view
        if found_commentnotifications_url(page.mainFrame().url()):
            view.close()
            
    qu(page, load_progress=load_progress, load_finished=load_finished)

    view = qu(QWebView, page=page)
    page.mainFrame().load(url)
    view.show()
    return True

def found_commentnotifications_url(url):
    if url and url.path().rstrip('/').endswith('/commentnotifications') and not url.path().startswith('/my'):
        global user_url
        user_url = url.toString().split('?')[0]
        with open('settings/user.txt', 'w') as f:
            f.write(user_url)
        start()
        return True
    return False


def finished(reply):
    redirect_url = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
    if redirect_url and found_commentnotifications_url(redirect_url):
        pass
    elif redirect_url and found_login_url(redirect_url):
        pass
    elif redirect_url:
        send_request(redirect_url)
    elif reply.url().path().rstrip('/').endswith('/commentnotifications'):
        data = reply.readAll().data()
        _callback(parse_commentnotifications(data))
    else:
        print("Don't know what to do with URL", reply.url().toString())


def send_request(url, callback=finished):
    global reply
    request = QNetworkRequest(QUrl(url))
    reply = nam.get(request)
    reply.finished.connect(lambda: callback(reply))


def update(reset_timer=True):
    send_request(user_url+'?l=english')

    if reset_timer:
        timer.start()

def start():
    global timer
    timer = qu(QTimer, interval=1000*30, timeout=lambda: update(False))
    timer.start()
    update(False)

def run(result_callback=lambda: None):
    global _callback
    _callback = result_callback
    try:
        global user_url
        with open('settings/user.txt') as f:
            user_url = f.read()
    except OSError:
        send_request('http://steamcommunity.com/my/commentnotifications')
    else:
        start()