#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  app.py
#  

import yaml
from flask import Flask
from healthcheck import HealthCheck

from database import db_session, init_db
from vrt_metadata_updater import VrtMetadataUpdater

app = Flask(__name__)

health = HealthCheck()

DEFAULT_CFG_FILE = "./config.yml"

# Load config file
with open(DEFAULT_CFG_FILE, "r") as ymlfile:
    cfg: dict = yaml.load(ymlfile, Loader=yaml.FullLoader)

@app.route("/start", methods=["POST"])
def start() -> str:
    """Starts the metadata updater with supplied config."""
    vrt_metadata_updater = VrtMetadataUpdater(cfg)
    try:
        vrt_metadata_updater.start()
    except Exception as e:
        return f"An error has occured. {e}"
    return "Requested an update for all items."


@app.route("/progress", methods=["GET"])
def get_progress() -> str:
    """Gets the current progress by giving the amount of items in each status."""
    vrt_metadata_updater = VrtMetadataUpdater(cfg)

    return vrt_metadata_updater.get_progress()


@app.teardown_appcontext
def shutdown_session(exception=None) -> None:
    db_session.remove()
    

def database_available():
    return True, "database ok"


def config_available():
    return True, "config ok"


def mediahaven_connection_possible():
    return True, "mediahaven ok"

health.add_check(database_available)
health.add_check(config_available)
health.add_check(mediahaven_connection_possible)


app.add_url_rule("/health", "healthcheck", view_func=lambda: health.run())

if __name__ == '__main__':
    # Init database to make sure file and tables exist
    init_db()
    app.run(host="0.0.0.0", debug=True) 
