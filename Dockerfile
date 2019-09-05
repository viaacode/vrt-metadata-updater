FROM python:3.7
ENV USER=rudolf
ENV UID=12006
ENV GID=12006
RUN addgroup --gid "$GID" "$USER" \
    && adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --ingroup "$USER" \
    --uid "$UID" \
    "$USER"
WORKDIR /app
COPY . .
RUN chown rudolf:rudolf -R .
USER rudolf
RUN pip install --no-cache-dir -r requirements.txt --user
ENV PATH "$PATH:/app/.local/bin"
EXPOSE 5000
CMD ["uwsgi", "app_uwsgi.ini"]
