FROM python:3.7
VOLUME /usr/src/app/public
WORKDIR /usr/src/app
ENV USER=rudolf
ENV UID=12006
ENV GID=12006
RUN addgroup --gid "$GID" "$USER" \
    && adduser \
    --disabled-password \
    --gecos "" \
    --home "$(pwd)" \
    --ingroup "$USER" \
    --no-create-home \
    --uid "$UID" \
    "$USER"
COPY . .
RUN rm -rf public/*
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod -R 775 .
RUN chown rudolf:rudolf -R .
USER rudolf
ADD ./app.py /app/app.py
ADD ./app_uwsgi.ini /app/app_uwsgi.ini
ADD ./app_uwsgi.py /app/app_uwsgi.py
ENV PATH "$PATH:/app/.local/bin"
EXPOSE 5000
CMD ["uwsgi", "app_uwsgi.ini"]
