import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import requests
import json
import os
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
import time

# Constants for caching and radius
CACHE_FILE = "mosque_data.json"
CACHE_RADIUS = 30000  # 30 kilometers
UPDATE_DISTANCE = 20000  # 20 kilometers
PRAYER_BUFFER_MINUTES = 5  # Number of minutes before prayer to wake up
SILENCE_DURATION = 30  # Number of minutes to silence the phone after prayer

# Function to calculate distance using the Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c  # Distance in kilometers
    return distance * 1000  # Convert to meters

# Function to fetch prayer times using a Prayer Times API
def fetch_prayer_times(latitude, longitude, api_key):
    prayer_time_api_url = f"http://api.aladhan.com/v1/timings/{int(datetime.now().timestamp())}?latitude={latitude}&longitude={longitude}&method=2"
    response = requests.get(prayer_time_api_url)
    prayer_times = response.json()['data']['timings']
    
    # Convert prayer times to datetime objects for comparison
    prayer_times = {
        prayer: datetime.strptime(prayer_times[prayer], "%H:%M")
        for prayer in prayer_times
    }
    
    return prayer_times

# Function to fetch mosque locations within a 30 km radius from OpenStreetMap (OSM) using Overpass API
def fetch_mosque_locations(lat, lon, radius=CACHE_RADIUS):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    node["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
    out body;
    """
    response = requests.get(overpass_url)
    if response.status_code == 200:
        data = response.json()
        mosques = [
            {
                "name": element.get("tags", {}).get("name", "Unnamed Mosque"),
                "lat": element["lat"],
                "lon": element["lon"]
            }
            for element in data['elements'] if 'lat' in element and 'lon' in element
        ]
        return mosques
    else:
        return []

# Function to cache mosque data locally
def cache_mosque_data(mosques, lat, lon):
    cache_data = {
        "mosques": mosques,
        "last_lat": lat,
        "last_lon": lon,
        "last_update": str(datetime.now().date())  # Store the date of the last update
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f)

# Function to load cached mosque data
def load_cached_mosque_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

# Function to check if cache needs to be updated based on location
def should_update_cache(current_lat, current_lon, cached_data):
    last_lat = cached_data.get("last_lat")
    last_lon = cached_data.get("last_lon")
    last_update = cached_data.get("last_update")
    
    # Calculate distance from last cached location
    distance = haversine(current_lat, current_lon, last_lat, last_lon)
    
    # Check if the device has moved more than 20 km since the last cache update
    if distance > UPDATE_DISTANCE:
        return True
    
    # Optionally, check if the last update was more than a day ago
    if datetime.now().date() > datetime.strptime(last_update, '%Y-%m-%d').date():
        return True
    
    return False

# Function to schedule wake-up calls for prayers
def schedule_prayer_alarms(prayer_times):
    for prayer, time in prayer_times.items():
        # Calculate the alarm time (5 minutes before each prayer)
        alarm_time = time - timedelta(minutes=PRAYER_BUFFER_MINUTES)
        
        # Schedule the alarm using platform-specific APIs
        # For Android, use AlarmManager, or for other platforms, adjust accordingly
        # Here we'll just simulate it with a placeholder
        print(f"Scheduled alarm for {prayer} at {alarm_time}")

# BeeWare App Class
class MosqueApp(toga.App):

    def startup(self):
        # Main window setup
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Create widgets
        self.location_label = toga.Label('Fetching location...')
        self.prayer_time_label = toga.Label('Fetching prayer times...')
        self.mosque_label = toga.Label('Mosque status: Not checked yet.')
        self.cache_status_label = toga.Label('Cache status: Not loaded yet.')
        self.refresh_button = toga.Button('Refresh', on_press=self.refresh_data, style=Pack(padding=10))

        # Layout configuration
        box = toga.Box(
            children=[
                self.location_label,
                self.prayer_time_label,
                self.mosque_label,
                self.cache_status_label,
                self.refresh_button
            ],
            style=Pack(direction=COLUMN, padding=10)
        )
        
        # Set the content of the main window
        self.main_window.content = box
        self.main_window.show()

        # Check for location permission
        self.request_location_permission()

    def request_location_permission(self):
        # Code to request location permission from the user
        # Replace with platform-specific code to request location permission
        self.location_label.text = 'Location permission granted.'

        # Dummy location for demonstration (replace with actual location fetching)
        self.user_lat = 24.7136  # Example: Riyadh
        self.user_lon = 46.6753

        # Fetch prayer times and schedule alarms
        self.fetch_prayer_times_and_schedule_alarms()

    def fetch_prayer_times_and_schedule_alarms(self):
        # Fetch prayer times using the API
        prayer_times_api_key = "your_prayer_times_api_key"
        prayer_times = fetch_prayer_times(self.user_lat, self.user_lon, prayer_times_api_key)

        # Display the next prayer time
        next_prayer = min(prayer_times, key=lambda p: prayer_times[p])
        self.prayer_time_label.text = f"Next prayer: {next_prayer}"

        # Schedule alarms for all prayer times
        schedule_prayer_alarms(prayer_times)

    def refresh_data(self, widget):
        # Function to refresh data manually (if needed)
        pass


# Main function to start the app
def main():
    return MosqueApp()

if __name__ == '__main__':
    main().main_loop()
