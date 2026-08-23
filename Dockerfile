FROM python:3.12-slim

WORKDIR /aplicacao

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check \
    --root-user-action=ignore -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/aplicacao/src

CMD ["python", "-m", "churn.treinar"]
