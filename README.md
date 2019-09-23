# VRT Metadata Updater

Gets all fragments for a given type from mediahaven and requests a metadata update.

## Prerequisites

- Python 3.7
- Sqlite

### Optional

- Docker

## Installation

### With Docker
1. Clone or download the repository
2. `cd` into the directory
3. Add `config.yml` and fill it with credentials and mediatype (see `config.yml.example` for format)
4. Run `docker build . -t vrt-metadata-updater`
5. Check with `docker images list` if the image was created succesfully.

### Without Docker
1. Clone or download the repository
2. `cd` into the directory
3. Add `config.yml` and fill it with credentials and mediatype (see `config.yml.example` for format)
4. Create a virtual environment `python -m venv .`
5. Activate the environment `source bin/activate` on Linux or `Scripts/activate` on Windows.
6. Install dependencies `pip install -r requirements.txt`

## Usage

### Starting the service

#### With Docker

Run `docker run -p 5000:5000 vrt-metadata-updater`

#### Without Docker

Run `python app.py`

### Using the service

To get the current progress, send a `GET` request to `http://0.0.0.0:5000/progress`

To start the service, send a `POST` request to `http://0.0.0.0:5000/start`

## Testing

1. Install test dependencies by running `pip install -r requirements-test.txt`
2. Run the unit tests with `python -m pytest ./tests` from within the root folder.
3. For a code coverage report run `python -m pytest --cov=vrt_metadata_updater --cov-report html tests/`
