FROM ubuntu

COPY *.py /
COPY static /
COPY templates /
COPY requirements.txt /
COPY server.py /

RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install -r requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV FLASK_APP server.py

CMD ["flask", "run", "--host", "0.0.0.0"]
