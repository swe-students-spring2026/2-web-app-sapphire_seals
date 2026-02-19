FROM python:3.12

WORKDIR /usr/src/app/

# order of operations issue

COPY ./requirements.txt /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "app.py" ]