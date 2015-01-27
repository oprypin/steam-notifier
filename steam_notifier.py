#!/usr/bin/env python

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


import sys
import os
import os.path


try:
    script_name = __FILE__
except NameError:
    script_name = sys.argv[0]
os.chdir(os.path.dirname(os.path.realpath(os.path.abspath(script_name))))


sys.path.insert(0, 'universal-qt')


from traceback import print_exception

def my_excepthook(type, value, traceback):
    sys.__excepthook__(type, value, traceback)
    try:
        with open('error_log.txt', 'a') as f:
            print_exception(type, value, traceback, file=f)
    except Exception:
        pass

sys.excepthook = my_excepthook


import app