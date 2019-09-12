# VRT Metadata Updater

Gets all fragments for a given type from mediahaven and requests a metadata update

## Prerequisites

- Python 3.7
- Sqlite

### Optional

- Docker

## Installation

### With Docker
1. clone or download the repository
2. `cd` into the directory
3. add `config.yml` and fill it with credentials and mediatype (see `config.yml.example` for format)
4. run `docker build . -t vrt-metadata-updater`
5. check with `docker images list` if the image was created succesfully.

### Without Docker
1. clone or download the repository
2. `cd` into the directory
3. add `config.yml` and fill it with credentials and mediatype (see `config.yml.example` for format)
4. create a virtual environment `python -m venv env`
5. activate the environment `env\scripts\Activate.ps1` in powershell, `source env/bin/activate` in bash
6. install dependencies `pip install -r requirements.txt`

## Usage

### Starting the service

#### With Docker

run `docker run -p 5000:5000 vrt-metadata-updater`

#### Without Docker

run `python app.py`

### Using the service

To get the current progress, send a `GET` request to `http://0.0.0.0:5000/progress`

To start the service, send a `POST` request to `http://0.0.0.0:5000/start`

## Testing

You can run the unit tests with `python -m pytest` from within the root folder.