FROM python:alpine3.7
ARG APIKEY
ARG WEATHER_COUNTRY
ARG WEATHER_LANGUAGE
ARG PROMETHEUS_PORT

RUN pip install --upgrade pip && pip uninstall serial

COPY files/requirements.txt /app/

WORKDIR /app
RUN pip install -r requirements.txt

RUN mkdir -p /data/backup

COPY files/app* /app/

CMD python ./openweathermap-export.py