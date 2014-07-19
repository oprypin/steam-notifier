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


from qt.network import QNetworkCookieJar, QNetworkCookie

class PersistentCookieJar(QNetworkCookieJar):
    def __init__(self, filename):
        QNetworkCookieJar.__init__(self)
        self.filename = filename
        try:
            with open(self.filename, 'rb') as f:
                self.setAllCookies([c for data in f.read().split(b'\n\n') for c in QNetworkCookie.parseCookies(data)])
        except FileNotFoundError:
            pass
    
    def setCookiesFromUrl(self, cookies, url):
        result = QNetworkCookieJar.setCookiesFromUrl(self, cookies, url)
        with open(self.filename, 'wb') as f:
            for cookie in self.allCookies():
                f.write(cookie.toRawForm().data())
                f.write(b'\n\n')
        return result