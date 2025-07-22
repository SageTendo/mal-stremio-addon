FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
COPY . .

EXPOSE 5000

RUN apt-get update && apt-get install -y \
    python3-pip \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN pip install pipenv \
    && pipenv requirements > requirements.txt \
    && pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["run.py"]
