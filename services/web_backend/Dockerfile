# pull official base image
FROM python:3.9.5

# set work directory
WORKDIR /usr/src/backend

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y netcat

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/backend/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/backend/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/backend/entrypoint.sh"]
