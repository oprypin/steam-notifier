# Steam Notifier


## Introduction

*Steam Notifier* is a cross-platform application that shows [notifications](http://steamcommunity.com/my/commentnotifications/) from Steam Community in a system tray icon.

[![Screenshot](http://i.imgur.com/T5Q9XEB.png)](http://imgur.com/a/nI9hs)

Its obvious advantage is that you don't need to activate Steam's main window to check for notifications.

It is highly configurable, and allows you to react to notifications differently depending on filters:

- Ignore  
  (don't show in Steam Notifier, but leave the notification in Steam)
- Mark as read  
  (this is pre-configured for unwanted trading messages and *"This item has been deleted"*)
- Show a popup notification  
  (pre-configured to notify about replies to your own items, replies on others' profiles or statuses, and offline messages)

[The configuration file](settings/config.py) is actually a script in Python programming language, but it is quite easy to understand. This takes the configurability to a whole new level (see the [wiki](https://github.com/BlaXpirit/steam-notifier/wiki) to get some ideas).


## Instructions

This program works by simulating a web browser and downloading <http://steamcommunity.com/my/commentnotifications> every 30 seconds. The page is then parsed to get the information about new comments you got in Steam Community as well as other events.

In order to do this, *Steam Notifier* will need you to login to Steam Community in the browser window that will be shown to you. Of course, entering your password in some suspicious looking window can be a risk. But this program does not store your login data in any way. The program's source code is available in its entirety.

The initial setup ends successfully when you reach your comment notifications page, and if everything goes well, you should be redirected there automatically after you log in. You may need to log in again from time to time if the session expires.

Afterwards, *Steam Notifier* will consist only of the system tray (notification area) icon with the number of new events (if any) on it, very similarly to the one you get inside Steam's main window. Right-clicking it will give you a menu with some self-explanatory options (including *Quit*), and also individual event groups. Clicking on the events in the menu will open the corresponding part of Steam Community website in your default browser. Double clicking the icon will select the first available event from that menu and send you to it.

Make sure to check out [settings/config.py](settings/config.py) to configure filtering, notification popups and much more. The application must be restarted to reload the configuration.


## Installation

- **Windows**

  Download the latest binary win32 [release](https://github.com/BlaXpirit/steam-notifier/releases), extract the folder and you're ready to go!

  If you don't trust the *.exe*, you can [download Python](https://www.python.org/downloads/) 3.x, install it and use *steam_notifier.pyw* directly. The needed libraries are included with the binary release, but you may choose to install them yourself (see the list below) and use the source release.

- **Linux**

  Download the latest source [release](https://github.com/BlaXpirit/steam-notifier/tags) and extract the folder.

  Install the libraries: (`python-pyside` or `python-pyqt4`), `python-lxml`, `python-cssselect`. `libqtwebkit4`/`qt4-webkit`/etc and `sni-qt` may be needed.
  
- **Mac**
  
  *Steam Notifier* should work under Mac if the needed libraries are available. Try to adapt the instructions for Linux.


## Technical Details

*Steam Notifier* is written using the [Python programming language](http://python.org/), [Qt](http://qt-project.org/) and [lxml](http://lxml.de/).

It is guaranteed to work on Python 3.4 and later; Versions 2.7 and 3.3 also work but aren't tested very often.

*Steam Notifier* supports Qt 4 and Qt 5, and can work with either [PySide](http://pyside.org/), [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/download) or [PyQt5](http://www.riverbankcomputing.co.uk/software/pyqt/download5) (in this order of preference).

Internet access is done using *QNetworkAccessManager* with cookies saved to a text file, and the browser window bases on it and uses *QtWebKit* (yes, a full browser engine is used...).

License: GNU General Public License Version 3.0 (GPLv3)
