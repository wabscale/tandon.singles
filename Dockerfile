FROM jmc1283/flasq-base

RUN apk add --no-cache --update mysql-client

COPY ./requirements.txt /flasq/
RUN pip3 install -r /flasq/requirements.txt
RUN mkdir -p /flasq/web/.data/

COPY . /flasq

CMD ["./entrypoint.sh"]
