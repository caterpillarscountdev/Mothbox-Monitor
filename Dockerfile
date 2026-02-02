FROM python:3.13-slim
COPY requirements.txt /
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["./docker_run.sh"]
