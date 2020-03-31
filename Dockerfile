FROM python:3.8-slim-buster as base
FROM base as builder

RUN mkdir -p /base
RUN mkdir -p /python
WORKDIR /base/

COPY *.py .
COPY app app/
COPY static static/
COPY requirements.txt requirements.txt
COPY server.py server.py

RUN apt-get update && apt-get install -y nodejs yarn gcc gfortran python-dev libblas-dev liblapack-dev libatlas-base-dev cython
RUN pip install --target=/python -r /requirements.txt

ARG PORT

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV REACT_APP_SERVER_URI 'http://localhost'
ENV REACT_APP_PORT=$PORT

WORKDIR /base/app/

CMD ["yarn"]
CMD ["yarn", "build"]

COPY /base/app/build/* /base/static/

#######################################################################

FROM base

ARG SECRET_KEY

ENV FLASK_APP server.py
ENV SECRET_KEY $SECRET_KEY

COPY --from=builder /install /usr/local
COPY --from=builder /base /app

WORKDIR /app

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku
CMD gunicorn --bind 0.0.0.0:$PORT server:app 
