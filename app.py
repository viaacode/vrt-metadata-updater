#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  app.py
#  

from flask import Flask

import vrt_metadata_updater
from database import db_session, init_db

app = Flask(__name__)


@app.route("/start", methods=["POST"])
def start():
    try:
        vrt_metadata_updater.start()
    except Exception as e:
        return False
    return True


@app.route("/progress", methods=["GET"])
def get_progress():
    return vrt_metadata_updater.get_progress()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    print("starting flask")
    init_db()
    app.run(host="0.0.0.0", debug=True) 
