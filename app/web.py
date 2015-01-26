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

    view = qu(QWebView, page=page, window_title="Steam Notifier")
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
        request(redirect_url, finished)
    elif reply.url().path().rstrip('/').endswith('/commentnotifications'):
        data = reply.readAll().data()
        _callback(parse_commentnotifications(data))
    else:
        print("Don't know what to do with URL", reply.url().toString())



def _do_request(url, callback=None):
    print(url)
    if isinstance(url, tuple):
        url, data = url
    else:
        data = None
    global reply
    request = QNetworkRequest(QUrl(url))
    if data is not None:
        reply = nam.post(request, data)
    else:
        reply = nam.get(request)
    if callback is not None:
        reply.finished.connect(lambda: callback(reply))

request_queue = None

def request(url, callback=None):
    global request_queue
    if request_queue is None:
        request_queue = [(url, callback)]
        _next_request()
        request_timer.start()
    else:
        request_queue.append((url, callback))

def _next_request():
    global request_queue
    if not request_queue:
        request_queue = None
    else:
        _do_request(*request_queue.pop(0))

request_timer = qu(QTimer, interval=1000*2, timeout=_next_request)


def update(reset_timer=True):
    request(user_url+'?l=english', finished)

    if reset_timer:
        timer.start()

timer = qu(QTimer, interval=1000*30, timeout=lambda: update(False))

def start():
    update()

def run(result_callback=lambda: None):
    global _callback
    _callback = result_callback
    try:
        global user_url
        with open('settings/user.txt') as f:
            user_url = f.read()
    except OSError:
        request('http://steamcommunity.com/my/commentnotifications', finished)
    else:
        start()