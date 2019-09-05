# VRT Metadata Updater

Gets all fragments for a given type from mediahaven and requests a metadata update

## Prerequisites

- Docker

## Installation

1. Clone or download the repository
2. `cd` into the directory
3. add `config.yml` and fill it with credentials and mediatype (see `config.yml.example` for format)
4. run `docker build . -t vrt-metadata-updater`

## Usage
### Starting the service

run `docker run -p 5000:5000 vrt-metadata-updater`

### Using the service

To get the current progress, send a `GET` request to `http://0.0.0.0:5000/progress`

To start the service, send a `POST` request to `http://0.0.0.0:5000/start`
