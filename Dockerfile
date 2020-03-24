FROM ubuntu

COPY *.py /
COPY app/ /app/
COPY static/ /static/
COPY requirements.txt /
COPY server.py /

RUN apt-get update && apt-get install -y python3-pip nodejs npm
RUN pip3 install -r requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV FLASK_APP server.py

WORKDIR /app
RUN ls -l /app
CMD ["npm", "install"]
CMD ["npm", "run", "build"]

WORKDIR /
RUN ls -l /
COPY /app/build/* /static/
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5001"]
