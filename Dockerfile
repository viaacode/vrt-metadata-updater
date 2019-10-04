FROM python:3.7-alpine3.10

RUN apk add --no-cache \
        uwsgi-python3

# add python to path otherwise uwsgi will not find flask package
ENV PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.7/site-packages:/usr/lib/python3.7/site-packages

VOLUME /usr/src/app/public
WORKDIR /usr/src/app

COPY . .
RUN pip3 install -r requirements.txt

# Create database file if it doesn't exist and allow read/write
RUN touch database.db
RUN chmod a+rw database.db
RUN chmod 775 .

EXPOSE 5000

# Run the application
ENTRYPOINT ["python"]
CMD ["vrt_metadata_updater.py"]
