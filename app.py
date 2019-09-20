#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Rudolf De Geijter
#
#  app.py
#  

import yaml
from flask import Flask
from healthcheck import EnvironmentDump, HealthCheck

from database import db_session, init_db, engine
from vrt_metadata_updater import VrtMetadataUpdater

app = Flask(__name__)

readiness = HealthCheck()
liveness = EnvironmentDump()

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
    table_exists = engine.dialect.has_table(engine, 'media_objects')
    return table_exists, "database exists with table media_objects"


def config_available():
    return bool(cfg), "configfile is not empty"


readiness.add_check(database_available)
readiness.add_check(config_available)

app.add_url_rule("/readiness", "readiness", view_func=lambda: readiness.run())
app.add_url_rule("/liveness", "liveness", view_func=lambda: liveness.run())

if __name__ == '__main__':
    # Init database to make sure file and tables exist
    init_db()
    app.run(host="0.0.0.0", debug=True) 
