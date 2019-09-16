#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  app.py
#  

from flask import Flask
import yaml


from vrt_metadata_updater import VrtMetadataUpdater
from database import db_session, init_db

app = Flask(__name__)

DEFAULT_CFG_FILE = "./config.yml"

@app.route("/start", methods=["POST"])
def start():
    vrt_metadata_updater = VrtMetadataUpdater(cfg)
    try:
        vrt_metadata_updater.start()
    except Exception as e:
        return False
    return True


@app.route("/progress", methods=["GET"])
def get_progress():
    vrt_metadata_updater = VrtMetadataUpdater(cfg)

    return vrt_metadata_updater.get_progress()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    # Load config file
    with open(DEFAULT_CFG_FILE, "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    # Init database to make sure file and tables exist
    init_db()
    app.run(host="0.0.0.0", debug=True) 
