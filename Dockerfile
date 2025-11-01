FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
COPY . .

EXPOSE 5000

RUN pip install pipenv \
    && pipenv requirements > requirements.txt \
    && pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["run.py"]
