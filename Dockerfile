FROM python:3.10-slim

LABEL authors="iratatuii"

WORKDIR /app

COPY . /app

RUN pip install poetry

RUN poetry install --no-dev

CMD ["poetry", "run", "flask", "run", "--host=0.0.0.0"]

ENTRYPOINT ["top", "-b"]