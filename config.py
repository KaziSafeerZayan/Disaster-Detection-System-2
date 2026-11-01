"""
Global Configuration and Region Presets for Flood & Earthquake Early Warning System.
"""

# Google Cloud Project ID for Earth Engine
GEE_PROJECT_ID = "flood-warning-system-511803"

# Public token placeholder if needed (Esri satellite tiles used by default require no token)
MAPBOX_PUBLIC_TOKEN = "your-mapbox-token-here"

# Global Regions including International Hotspots and All Divisions of Bangladesh
GLOBAL_REGIONS = {
    # --- 🇧🇩 All 8 Divisions of Bangladesh ---
    "Dhaka Division, Bangladesh": {
        "lat": 23.8103,
        "lon": 90.4125,
        "zoom": 10,
        "bbox": [90.20, 23.60, 90.60, 24.00],
        "pop": 36000000
    },
    "Chattogram Division, Bangladesh": {
        "lat": 22.3569,
        "lon": 91.7832,
        "zoom": 10,
        "bbox": [91.70, 22.20, 91.95, 22.55],
        "pop": 30000000
    },
    "Rajshahi Division, Bangladesh": {
        "lat": 24.3745,
        "lon": 88.6042,
        "zoom": 10,
        "bbox": [88.50, 24.30, 88.75, 24.50],
        "pop": 20000000
    },
    "Khulna Division, Bangladesh": {
        "lat": 22.8456,
        "lon": 89.5403,
        "zoom": 10,
        "bbox": [89.40, 22.70, 89.70, 22.95],
        "pop": 17000000
    },
    "Sylhet Division, Bangladesh": {
        "lat": 24.8949,
        "lon": 91.8687,
        "zoom": 10,
        "bbox": [91.80, 24.80, 91.98, 25.00],
        "pop": 11000000
    },
    "Barishal Division, Bangladesh": {
        "lat": 22.7010,
        "lon": 90.3535,
        "zoom": 10,
        "bbox": [90.25, 22.60, 90.48, 22.82],
        "pop": 9000000
    },
    "Rangpur Division, Bangladesh": {
        "lat": 25.7439,
        "lon": 89.2752,
        "zoom": 10,
        "bbox": [89.15, 25.65, 89.40, 25.85],
        "pop": 17000000
    },
    "Mymensingh Division, Bangladesh": {
        "lat": 24.7471,
        "lon": 90.4203,
        "zoom": 10,
        "bbox": [90.30, 24.65, 90.55, 24.85],
        "pop": 12000000
    },

    # --- 🌍 International Flood & Waterlogging Zones ---
    "Venice, Italy": {
        "lat": 45.4408,
        "lon": 12.3155,
        "zoom": 12,
        "bbox": [12.25, 45.40, 12.38, 45.48],
        "pop": 250000
    },
    "Amsterdam, Netherlands": {
        "lat": 52.3676,
        "lon": 4.9041,
        "zoom": 12,
        "bbox": [4.82, 52.30, 4.98, 52.42],
        "pop": 872000
    },

    # --- 🌋 International Earthquake Zones ---
    "Tokyo, Japan": {
        "lat": 35.6762,
        "lon": 139.6503,
        "zoom": 11,
        "bbox": [139.50, 35.55, 139.85, 35.80],
        "pop": 14000000
    },
    "San Francisco, USA": {
        "lat": 37.7749,
        "lon": -122.4194,
        "zoom": 12,
        "bbox": [-122.52, 37.70, -122.35, 37.83],
        "pop": 873965
    },
    "Istanbul, Turkey": {
        "lat": 41.0082,
        "lon": 28.9784,
        "zoom": 11,
        "bbox": [28.80, 40.90, 29.15, 41.12],
        "pop": 15840900
    },
    "Santiago, Chile": {
        "lat": -33.4489,
        "lon": -70.6693,
        "zoom": 11,
        "bbox": [-70.80, -33.58, -70.50, -33.35],
        "pop": 6257516
    },
    "Wellington, New Zealand": {
        "lat": -41.2866,
        "lon": 174.7756,
        "zoom": 12,
        "bbox": [174.70, -41.35, 174.88, -41.22],
        "pop": 212700
    }
}