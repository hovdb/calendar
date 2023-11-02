FROM alpine:latest
COPY . /calendar
WORKDIR /calendar
# Install required packages (Alpine uses busybox-cron)
RUN apk update && apk add python3 py3-pip busybox-extras



RUN apk add --no-cache --update \
    python3 \
    py3-pip
    
    

RUN pip install --upgrade pip
RUN pip install -r requirements.txt


EXPOSE 8000
ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]