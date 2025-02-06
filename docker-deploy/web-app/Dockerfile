FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/
COPY credentials.json /code/credentials.json
COPY token.json /code/token.json
COPY initserver.sh /initserver.sh
