#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  app_uwsgi.py
#  

from app import app as application
from database import init_db

init_db()
