from flask import Flask
from database import db_session, init_db
import vrt_metadata_updater

app = Flask(__name__)


@app.route("/start", methods=["POST"])
def start():
    return vrt_metadata_updater.start()


@app.route("/progress")
def get_progress():
    return vrt_metadata_updater.get_progress()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", debug=True) 