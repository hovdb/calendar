FROM alpine:latest

COPY . /calendar
WORKDIR /calendar

# Install system dependencies
# Consolidating apk add but keeping your structure for python3 and py3-pip
RUN apk update && \
    apk add --no-cache python3 py3-pip busybox-extras

# Upgrade pip (using pip3)
RUN pip3 install --upgrade pip --break-system-packages

# Install Python dependencies
RUN pip3 install --break-system-packages -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]