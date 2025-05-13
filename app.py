from flask import Flask, render_template, send_from_directory, jsonify
import requests
from ics import Calendar
from datetime import datetime, timedelta, date
import os
import pytz

app = Flask(__name__, static_url_path='/static')

# --- Configuration File Paths ---
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'static', 'config')
API_KEY_FILE = os.path.join(CONFIG_DIR, 'weather_api_key.txt')
GEO_COORDS_FILE = os.path.join(CONFIG_DIR, 'geo_coordinates.txt')
ICS_URLS_FILE = os.path.join(os.path.dirname(__file__), 'static', 'ics', 'ics_urls.txt')

# --- Function to read Weather API Key ---
def read_weather_api_key(file_path):
    try:
        with open(file_path, 'r') as file:
            key = file.read().strip()
            if key:
                print(f"DEBUG: Successfully read Weather API Key from {file_path}")
                return key
            else:
                print(f"ERROR: Weather API Key file {file_path} is empty.")
                return None
    except FileNotFoundError:
        print(f"ERROR: Weather API Key file not found at {file_path}. Please create it.")
        return None
    except Exception as e:
        print(f"ERROR: Could not read Weather API Key from {file_path}: {e}")
        return None

# --- Function to read Geo Coordinates ---
def read_geo_coordinates(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                lat_str = lines[0].strip()
                lon_str = lines[1].strip()
                try:
                    lat = float(lat_str)
                    lon = float(lon_str)
                    print(f"DEBUG: Successfully read Geo Coordinates (Lat: {lat}, Lon: {lon}) from {file_path}")
                    return lat, lon
                except ValueError:
                    print(f"ERROR: Geo Coordinates file {file_path} contains non-numeric values. Lat: '{lat_str}', Lon: '{lon_str}'")
                    return None, None
            else:
                print(f"ERROR: Geo Coordinates file {file_path} must contain at least two lines (latitude and longitude).")
                return None, None
    except FileNotFoundError:
        print(f"ERROR: Geo Coordinates file not found at {file_path}. Please create it.")
        return None, None
    except Exception as e:
        print(f"ERROR: Could not read Geo Coordinates from {file_path}: {e}")
        return None, None

# --- Load Configurations ---
WEATHER_API_KEY = read_weather_api_key(API_KEY_FILE)
GEO_LAT, GEO_LON = read_geo_coordinates(GEO_COORDS_FILE)

# Fallback to defaults if file reading fails (optional, or could make it critical)
if WEATHER_API_KEY is None:
    print("WARNING: Using default/empty Weather API Key. Weather widget may not work.")
    WEATHER_API_KEY = "YOUR_DEFAULT_API_KEY_HERE" # Or handle as a critical error

if GEO_LAT is None or GEO_LON is None:
    print("WARNING: Using default Geo Coordinates (Austin, TX). Weather widget may show incorrect location.")
    GEO_LAT = 30.2672  # Default Latitude (Austin)
    GEO_LON = -97.7431 # Default Longitude (Austin)

# Weather cache
weather_cache = {
    'data': None,
    'last_update': None
}

# Path to the folder containing images
image_folder = os.path.join(os.path.dirname(__file__), 'static', 'images')
image_list = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
current_image_index = 0

# Function to read ICS URLs from a file
def read_ics_urls_from_file(file_path):
    ics_urls = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                url = line.strip()
                if url:
                    ics_urls.append(url)
        print(f"DEBUG: Read {len(ics_urls)} URLs from {file_path}") # DEBUG PRINT
    except Exception as e:
        print(f"ERROR: Could not read ICS URLs file {file_path}: {e}")
    return ics_urls

# Read ICS URLs from the text file
ics_urls = read_ics_urls_from_file(ICS_URLS_FILE)

@app.route('/')
def index():
    events, calendars = get_events_from_ics_urls(ics_urls)
    # Sort events by a comparable datetime object before formatting
    # You'll need to adjust get_events_from_ics_urls to return sortable start times
    # For now, sorting by the formatted string (less reliable for date/time combined)
    events.sort(key=lambda x: x['start_time'], reverse=False) 
    return render_template('index.html', events=events, calendars=calendars)

@app.route('/get_image')
def get_image():
    global current_image_index
    
    if not image_list:
        return "No images found", 404
        
    # Get the current image
    current_image = image_list[current_image_index]
    current_image_index = (current_image_index + 1) % len(image_list)
    
    return send_from_directory(image_folder, current_image)

def fetch_weather_data():
    if not WEATHER_API_KEY or WEATHER_API_KEY == "YOUR_DEFAULT_API_KEY_HERE":
        print("ERROR: Weather API Key is not configured. Cannot fetch weather data.")
        return None
    if GEO_LAT is None or GEO_LON is None:
        print("ERROR: Geo coordinates are not configured. Cannot fetch weather data.")
        return None
        
    try:
        # Fetch current weather
        current_weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={GEO_LAT}&lon={GEO_LON}&appid={WEATHER_API_KEY}&units=imperial"
        current_response = requests.get(current_weather_url)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Fetch 5-day forecast with 3-hour intervals
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={GEO_LAT}&lon={GEO_LON}&appid={WEATHER_API_KEY}&units=imperial"
        forecast_response = requests.get(forecast_url)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        # Convert timestamps to Central time
        central_tz = pytz.timezone('US/Central')
        current_time = datetime.fromtimestamp(current_data['dt']).astimezone(central_tz)
        
        weather_data = {
            'current': {
                'temp': round(current_data['main']['temp']),
                'description': current_data['weather'][0]['description'],
                'icon': current_data['weather'][0]['icon'],
                'time': current_time.strftime('%I:%M %p'),
                'date': current_time.strftime('%a, %b %d')
            },
            'forecast': []
        }
        
        # Create a list of target times (current time + 4 hours, +8 hours, etc.)
        target_times = []
        for i in range(1, 7):  # 6 entries for 24 hours
            target_time = current_time + timedelta(hours=4*i)
            target_times.append(target_time)
        
        # Find the closest forecast entry for each target time
        for target_time in target_times:
            closest_forecast = min(forecast_data['list'], 
                key=lambda x: abs(datetime.fromtimestamp(x['dt']).astimezone(central_tz) - target_time))
            
            dt = datetime.fromtimestamp(closest_forecast['dt']).astimezone(central_tz)
            weather_data['forecast'].append({
                'temp': round(closest_forecast['main']['temp']),
                'description': closest_forecast['weather'][0]['description'],
                'icon': closest_forecast['weather'][0]['icon'],
                'time': target_time.strftime('%I:%M %p'),
                'date': target_time.strftime('%a, %b %d')
            })
        
        return weather_data
    except Exception as e:
        print(f"Error fetching weather: {str(e)}")
        return None

@app.route('/weather')
def get_weather():
    global weather_cache
    
    # Check if we need to update the cache
    now = datetime.now()
    if (weather_cache['last_update'] is None or 
        (now - weather_cache['last_update']).total_seconds() > 1800):  # 1800 seconds = 30 minutes
        
        # Fetch new weather data
        new_data = fetch_weather_data()
        if new_data:
            weather_cache['data'] = new_data
            weather_cache['last_update'] = now
        elif weather_cache['data'] is None:
            # If we have no data at all, return an error
            return jsonify({'error': 'Unable to fetch weather data'}), 500
    
    # Return cached data
    return jsonify(weather_cache['data'])

def get_events_from_ics_urls(ics_urls):
    central_timezone = pytz.timezone('US/Central')
    events = []
    calendars = [] # Initialize calendars list here

    # print(f"DEBUG: Starting event processing for {len(ics_urls)} URLs.") # Retain for high-level overview
    # print(f"DEBUG: URL List Type: {type(ics_urls)}")
    # print(f"DEBUG: URL List Content: {ics_urls}")

    for source, url in enumerate(ics_urls, 1):
        # print(f"DEBUG: >>> Entering loop for source {source}") # Commented out
        # print(f"\\nDEBUG: === PROCESSING URL #{source}: {url} ===") # Commented out
        calendar_name = f"Calendar {source}" # Default name
        try:
            # print(f"DEBUG: [{source}] Fetching calendar data...") # Commented out
            response = requests.get(url)
            # print(f"DEBUG: [{source}] Fetch successful (status {response.status_code}).") # Commented out
            response.raise_for_status()
            ics_text = response.text
            # print(f"DEBUG: [{source}] Got ICS text (length {len(ics_text)}).") # Commented out

            # --- Extract Calendar Name from Raw Text ---
            raw_name_found = False
            for line in ics_text.splitlines():
                if line.startswith('X-WR-CALNAME:'):
                    calendar_name = line.split(':', 1)[1].strip()
                    raw_name_found = True
                    # print(f"DEBUG: Found name '{calendar_name}' from raw text line.") # Commented out
                    break 
            
            c = Calendar(ics_text)
            # print(f"DEBUG: [{source}] Parsing ICS text with library...") # Commented out - this was before c = Calendar()
            # print(f"DEBUG: [{source}] ICS parsing complete.") # Commented out

            if not raw_name_found:
                # print("DEBUG: Raw text search did not find X-WR-CALNAME, trying library properties...") # Commented out
                if hasattr(c, 'extra_params') and 'X-WR-CALNAME' in c.extra_params:
                     cal_name_from_extra = c.extra_params['X-WR-CALNAME']
                     if cal_name_from_extra:
                         calendar_name = cal_name_from_extra
                elif hasattr(c, 'name') and c.name: 
                    calendar_name = c.name
            # print(f"DEBUG: Final Calendar Name for source {source}: '{calendar_name}'") # Commented out
            
            if not any(cal['source'] == source for cal in calendars):
                calendars.append({
                    'source': source,
                    'name': calendar_name,
                    'css_class': f'source-{source}'
                })
                # print(f"DEBUG: Added calendar {source} ({calendar_name}) to legend data.") # Commented out

            today = datetime.now().date()
            seven_days_later = today + timedelta(days=7)
            source_events = []

            # print(f"DEBUG: [{source}] Iterating through events in calendar '{calendar_name}'...") # Commented out
            event_count_in_cal = 0
            skipped_event_count = 0

            for event in c.events:
                event_count_in_cal += 1
                event_start_date = None
                if hasattr(event.begin, 'date'):
                    event_start_date = event.begin.date()
                elif isinstance(event.begin, datetime):
                    event_start_date = event.begin.date()
                
                if event_start_date is None or not (today <= event_start_date <= seven_days_later):
                    skipped_event_count += 1
                    continue

                # print("\\n" + "="*50) # Commented out event detail block
                # print(f"Event: {event.name}")
                # print(f"Raw begin: {event.begin}")
                # print(f"Raw end: {event.end}")
                
                is_all_day = False
                if hasattr(event, 'all_day') and event.all_day:
                    is_all_day = True
                elif isinstance(event.begin, date) and not isinstance(event.begin, datetime):
                    is_all_day = True

                # print(f"Is all-day event (Improved Check): {is_all_day}") # Commented out
                
                if is_all_day:
                    start_time_obj = event.begin if isinstance(event.begin, date) else event.begin.date()
                    start_time = start_time_obj.strftime('%B %d, %Y')
                    end_time_obj = event.end if isinstance(event.end, date) else event.end.date()
                    days = (end_time_obj - start_time_obj).days
                    # print(f"Days calculated: {days}") # Commented out
                    if days <= 1: 
                        duration = "All-Day"
                    else:
                         duration = f"{days} days"
                else:
                    start_dt = event.begin
                    end_dt = event.end
                    if start_dt.tzinfo is None: start_dt = pytz.utc.localize(start_dt)
                    if end_dt.tzinfo is None: end_dt = pytz.utc.localize(end_dt)
                    start_time_central = start_dt.astimezone(central_timezone)
                    end_time_central = end_dt.astimezone(central_timezone)
                    start_time = start_time_central.strftime('%B %d, %Y %I:%M %p')
                    duration_seconds = (end_time_central - start_time_central).total_seconds()
                    days = int(duration_seconds // (24 * 3600))
                    hours = int((duration_seconds % (24 * 3600)) // 3600)
                    minutes = int((duration_seconds % 3600) // 60)
                    duration_parts = []
                    if days > 0: duration_parts.append(f"{days} day{'s' if days > 1 else ''}")
                    if hours > 0: duration_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
                    if minutes > 0 and days == 0: duration_parts.append(f"{minutes} min")
                    duration = " ".join(duration_parts) if duration_parts else "Brief"
                
                # print(f"Start time: {start_time}") # Commented out event detail block
                # print(f"Duration: {duration}")
                # print("="*50)

                # print(f"FINAL CHECK BEFORE TEMPLATE:") # Commented out event detail block
                # print(f"  Event Name: {event.name}")
                # print(f"  Is All-Day: {is_all_day}")
                # print(f"  Formatted Start Time: {start_time}")
                # print(f"  Formatted Duration: {duration}")
                # print("="*50)

                # print(f"DEBUG: [{source}] Adding event '{event.name}' (Start: {start_time}) to list.") # Commented out
                source_events.append({
                    'summary': event.name,
                    'start_time': start_time, 
                    'duration': duration,
                    'source': f'{source}',
                    'is_all_day': is_all_day
                })
            
            # print(f"DEBUG: [{source}] Finished iterating. Processed {event_count_in_cal} events, added {len(source_events)} events within date range (skipped {skipped_event_count}).") # Commented out
            events.extend(source_events)

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to fetch ICS file for URL #{source} ({url}): {e}")
        except Exception as e:
            print(f"ERROR: Failed to parse ICS file for URL #{source} ({url}): {e}")
            import traceback
            print(traceback.format_exc())
        # print(f"DEBUG: <<< Exiting loop body for source {source}") # Commented out
        
    # Final sort of all events if needed
    # Requires storing a comparable datetime object for each event
    # events.sort(key=lambda x: x['start_time_obj']) 
        
    # --- Return events AND calendar legend data ---
    print(f"DEBUG: Finished processing. Found {len(events)} events total.") # Retain
    print(f"DEBUG: Final legend data contains {len(calendars)} calendars: {calendars}") # Retain
    return events, calendars

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
