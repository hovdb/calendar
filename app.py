from flask import Flask, render_template, send_from_directory
import requests
from ics import Calendar
from datetime import datetime, timedelta
import os
import pytz

app = Flask(__name__)

# Path to the folder containing images
image_folder = '/calendar/static/images'
image_list = os.listdir(image_folder)
current_image_index = 0

# Function to read ICS URLs from a file
def read_ics_urls_from_file(file_path):
    ics_urls = []
    with open(file_path, 'r') as file:
        for line in file:
            url = line.strip()
            if url:
                ics_urls.append(url)
    return ics_urls

# Read ICS URLs from the text file
ics_urls = read_ics_urls_from_file('/calendar/static/ics/ics_urls.txt')

@app.route('/')
def index():
    events = get_events_from_ics_urls(ics_urls)
    events.sort(key=lambda x: x['start_time'], reverse=False)
    return render_template('index.html', events=events)

@app.route('/get_image')
def get_image():
    global current_image_index

    # Get the current image
    image_path = os.path.join(image_folder, image_list[current_image_index])
    current_image_index = (current_image_index + 1) % len(image_list)

    return send_from_directory(image_folder, image_list[current_image_index])

def get_events_from_ics_urls(ics_urls):
    central_timezone = pytz.timezone('US/Central')  # Set to the appropriate time zone

    events = []

    # Get events from each ICS URL and organize them by source.
    for source, url in enumerate(ics_urls, 1):
        try:
            response = requests.get(url)
            response.raise_for_status()
            c = Calendar(response.text)

            today = datetime.now().date()
            seven_days_later = today + timedelta(days=7)

            source_events = []

            for event in c.events:
                if event.begin.date() >= today and event.begin.date() <= seven_days_later:
                    if event.duration == timedelta(days=1):
                        # Handle full-day events
                        start_time = event.begin.astimezone(central_timezone).strftime('%Y-%m-%d')
                        duration = "All-Day"
                    else:
                        start_time = event.begin.astimezone(central_timezone).strftime('%Y-%m-%d %H:%M:%S')
                        duration = (event.end - event.begin).seconds // 60

                    source_events.append({
                        'summary': event.name,
                        'start_time': start_time,
                        'duration': duration,
                        'source': f'{source}',
                    })
            events.extend(source_events)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching ICS file {url}: {e}")
        except Exception as e:
            print(f"Error parsing ICS file {url}: {e}")

    return events

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
