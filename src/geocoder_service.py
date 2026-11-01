"""
Smart Search & Geocoding Service using Nominatim and Geopy for Global Place Search.
"""
from geopy.geocoders import Nominatim

class GlobalGeocoder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="flood_early_warning_system_v2")

    def search_place(self, query: str):
        """
        Searches for any location worldwide and returns lat, lon, and bounding box.
        """
        try:
            location = self.geolocator.geocode(query, exactly_one=True, language="en")
            if location:
                lat = location.latitude
                lon = location.longitude
                # Construct approximate bounding box around point (~0.1 degree buffer)
                bbox = [lon - 0.1, lat - 0.1, lon + 0.1, lat + 0.1]
                return {
                    "name": location.address,
                    "lat": lat,
                    "lon": lon,
                    "bbox": bbox
                }
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None