import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.ndimage import gaussian_filter
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import warnings
import os
from datetime import datetime
from matplotlib.patches import Rectangle, Polygon

warnings.filterwarnings('ignore')

# Create frames directory if it doesn't exist
os.makedirs('frames', exist_ok=True)

# Vermont and NY cities/landmarks for map
VT_CITIES = {
    'Burlington': (-73.212, 44.476),
    'Montpelier': (-72.576, 44.260),
    'Rutland': (-72.973, 43.611),
    'St. Johnsbury': (-72.015, 44.419),
    'Lyndon': (-72.003, 44.534),
}

NY_CITIES = {
    'Plattsburgh': (-73.453, 44.695),
    'Lake Placid': (-73.983, 44.280),
    'Saranac Lake': (-74.131, 44.329),
}

def fetch_hrrr_data():
    """Fetch HRRR data from Open-Meteo API"""
    print("Fetching HRRR data from Open-Meteo...")
    
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 44.5337,
        "longitude": -72.0032,
        "hourly": ["temperature_2m", "cloud_cover", "wind_speed_10m", "surface_temperature", "precipitation"],
        "models": "gfs_hrrr",
        "timezone": "America/New_York",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "temperature_unit": "fahrenheit",
    }
    
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    
    return response

def draw_terrain_map(ax):
    """Draw a simplified terrain map with geographic features"""
    
    # Create terrain-like background using multiple overlapping gradients
    # Mountains (Green Mountains of VT, Adirondacks of NY)
    green_mountains = Polygon([(-72.9, 42.7), (-72.5, 43.0), (-72.3, 43.5), 
                               (-72.4, 44.0), (-72.5, 44.5), (-72.8, 44.8),
                               (-73.0, 44.5), (-73.1, 43.5), (-72.9, 42.7)],
                              facecolor='#2d5016', alpha=0.5, edgecolor='none', zorder=0)
    ax.add_patch(green_mountains)
    
    adirondacks = Polygon([(-74.5, 43.0), (-74.0, 43.5), (-73.5, 44.0),
                           (-73.7, 44.5), (-74.3, 44.8), (-75.0, 44.5),
                           (-75.2, 44.0), (-74.8, 43.2), (-74.5, 43.0)],
                          facecolor='#3d6026', alpha=0.5, edgecolor='none', zorder=0)
    ax.add_patch(adirondacks)
    
    # Lake Champlain (approximate shape)
    lake_champlain = Polygon([(-73.35, 43.6), (-73.30, 44.0), (-73.20, 44.5),
                              (-73.25, 44.8), (-73.35, 45.0), 
                              (-73.40, 44.8), (-73.45, 44.5), (-73.50, 44.0),
                              (-73.45, 43.6), (-73.35, 43.6)],
                             facecolor='#1e90ff', alpha=0.6, edgecolor='white', 
linewidth=1, zorder=1)
    ax.add_patch(lake_champlain)
    ax.text(-73.35, 44.3, 'Lake\nChamplain', fontsize=9, color='white', 
            ha='center', style='italic', weight='bold', zorder=2)
    
    # Connecticut River (VT/NH border)
    ax.plot([-72.1, -72.1, -72.0, -71.9, -71.8], 
            [42.0, 43.5, 44.0, 44.5, 45.0],
            color='cyan', linewidth=2, alpha=0.7, zorder=1, linestyle='-')
    
    # State boundaries (approximate)
    # VT western border
    ax.plot([-73.45, -73.40, -73.35, -73.30, -73.25, -73.35, -73.40],
            [42.75, 43.5, 44.0, 44.5, 45.0, 45.5, 45.5],
            color='white', linewidth=2.5, linestyle='--', alpha=0.8, zorder=2)
    
    # VT eastern border (Connecticut River)
    ax.plot([-72.1, -72.1, -72.0, -71.9, -71.8],
            [42.0, 43.5, 44.0, 44.5, 45.0],
            color='white', linewidth=2.5, linestyle='--', alpha=0.8, zorder=2)
    
    # Canadian border
    ax.plot([-76.5, -70.5], [45.0, 45.0], 
            color='red', linewidth=2, linestyle=':', alpha=0.7, zorder=2)
    ax.text(-73.5, 45.15, 'CANADA', fontsize=10, color='red', 
            ha='center', weight='bold', alpha=0.8, zorder=2)

def generate_hrrr_frame(frame_index=0, variable='temperature_2m'):
    """
    Generate a single HRRR forecast frame with terrain map
    
    Args:
        frame_index: which hour to display (0-11 for 12-hour loop)
        variable: 'temperature_2m', 'precipitation', 'cloud_cover', 'wind_speed_10m'
    """
    print(f"Generating frame {frame_index:02d}...")
    
    response = fetch_hrrr_data()
    hourly = response.Hourly()
    
    # Extract data based on variable
    variable_index = {
        'temperature_2m': 0,
        'cloud_cover': 1,
        'wind_speed_10m': 2,
        'surface_temperature': 3,
        'precipitation': 4
    }
    
    idx = variable_index.get(variable, 0)
    data_array = hourly.Variables(idx).ValuesAsNumpy()
    
    # Get the value for the requested frame
    value = data_array[frame_index]
    
    # Create date range and get current time
    time_range = pd.date_range(
        start=pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )
    current_time = time_range[frame_index]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10), facecolor='#1a1a1a')
    
    # Create terrain-colored background
    ax.set_facecolor('#0d1f2d')
    
    # Draw terrain map
    draw_terrain_map(ax)
    
    # Add gridlines
    ax.grid(True, linestyle='--', alpha=0.3, color='gray', linewidth=0.5, zorder=1)
    
    # Plot center observation point
    lat, lon = response.Latitude(), response.Longitude()
    color = get_color_for_value(value, variable)
    
    # Main observation point
    ax.scatter(lon, lat, s=1000, color=color, edgecolors='white', linewidth=4, 
               zorder=10, marker='o', label='VTSU Lyndon')
    
    # Add cities
    for city, (city_lon, city_lat) in VT_CITIES.items():
        if city == 'Lyndon':
            continue  # Already plotted as main point
        ax.scatter(city_lon, city_lat, s=100, color='yellow', marker='*', 
                   edgecolors='black', linewidth=0.5, zorder=9, alpha=0.8)
        ax.text(city_lon, city_lat-0.12, city, fontsize=8, color='white',
                ha='center', weight='bold', zorder=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6))
    
    for city, (city_lon, city_lat) in NY_CITIES.items():
        ax.scatter(city_lon, city_lat, s=80, color='orange', marker='s',
                   edgecolors='black', linewidth=0.5, zorder=9, alpha=0.8)
        ax.text(city_lon, city_lat-0.12, city, fontsize=7, color='white',
                ha='center', style='italic', zorder=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6))
    
    # Set map boundaries
    ax.set_xlim(-76.5, -70.5)
    ax.set_ylim(42.0, 45.5)
    ax.set_xlabel('Longitude', fontsize=11, color='white', weight='bold')
    ax.set_ylabel('Latitude', fontsize=11, color='white', weight='bold')
    
    # Make axis labels white
    ax.tick_params(colors='white', labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor('white')
        spine.set_linewidth(2)
    
    # Add state/region labels
    ax.text(-72.7, 44.8, 'VERMONT', fontsize=18, weight='bold', 
            color='white', alpha=0.9, ha='center',
            bbox=dict(boxstyle='round', facecolor='#00A5B3', alpha=0.8, edgecolor='white', linewidth=2),
            zorder=3)
    ax.text(-75.0, 43.8, 'NEW YORK', fontsize=16, weight='bold', 
            color='white', alpha=0.9, ha='center',
            bbox=dict(boxstyle='round', facecolor='#EC3754', alpha=0.8, edgecolor='white', linewidth=2),
            zorder=3)
    ax.text(-71.3, 43.2, 'NEW\nHAMPSHIRE', fontsize=11, weight='bold', 
            color='white', alpha=0.9, ha='center',
            bbox=dict(boxstyle='round', facecolor='#333', alpha=0.7, edgecolor='white'),
            zorder=3)
    
    # Add location annotation with arrow
    ax.annotate(f'VTSU Lyndon Weather Center\n{lat:.2f}°N, {lon:.2f}°W', 
                xy=(lon, lat), xytext=(lon-1.2, lat+0.7),
                fontsize=11, weight='bold', color='white',
                bbox=dict(boxstyle='round', facecolor='#00A5B3', alpha=0.95, 
                         edgecolor='white', linewidth=2),
                arrowprops=dict(arrowstyle='->', color='white', lw=3,
                               connectionstyle='arc3,rad=0.3'),
                zorder=11)
    
    # Add data value box
    title_text = format_title(variable, value)
    fig.suptitle(title_text, fontsize=19, weight='bold', color='white', y=0.98,
                bbox=dict(boxstyle='round', facecolor='#00A5B3', alpha=0.9, 
                         edgecolor='white', linewidth=2))
    
    # Add valid time and forecast hour
    time_text = f"Valid: {current_time.strftime('%a %b %d, %Y - %H:%M %Z')} | Forecast Hour +{frame_index:02d}"
    ax.text(0.5, 0.01, time_text, transform=ax.transAxes, 
            fontsize=12, color='white', ha='center', va='bottom', weight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.9, 
                     edgecolor='#00A5B3', linewidth=2), zorder=12)
    
    # Add legend
    add_legend(fig, ax, variable)
    
    # Add branding
    ax.text(0.01, 0.97, '© Vermont State University\nLyndon Weather Center', 
            transform=ax.transAxes, fontsize=9, color='white', 
            ha='left', va='top', alpha=0.8, style='italic', weight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.7), zorder=12)
    
    # Save figure
    filename = f'frames/frame_{frame_index:02d}.png'
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', dpi=150, facecolor='#1a1a1a', edgecolor='none')
    plt.close()
    
    print(f"✓ Frame saved: {filename}")
    return filename

def get_color_for_value(value, variable):
    """Get color based on value and variable"""
    if variable == 'temperature_2m' or variable == 'surface_temperature':
        # Cold (blue) to hot (red)
        if value < 0: return '#0066ff'  # blue
        elif value < 20: return '#00ccff'  # cyan
        elif value < 32: return '#00ff00'  # green
        elif value < 50: return '#ffff00'  # yellow
        elif value < 70: return '#ff8800'  # orange
        elif value < 85: return '#ff4400'  # red-orange
        else: return '#ff0000'  # red
    
    elif variable == 'precipitation':
        # Light to heavy rain
        if value < 0.01: return '#64b4ff'  # light blue (trace)
        elif value < 0.1: return '#00d632'  # green
        elif value < 0.25: return '#ffff00'  # yellow
        elif value < 0.5: return '#ff8800'  # orange
        elif value < 1.0: return '#ff0000'  # red
        else: return '#8b0000'  # dark red
    
    elif variable == 'cloud_cover':
        # Clear to overcast
        if value < 20: return '#FFD700'  # gold (sunny)
        elif value < 50: return '#87CEEB'  # sky blue (partly cloudy)
        elif value < 80: return '#b0b0b0'  # gray (mostly cloudy)
        else: return '#505050'  # dark gray (overcast)
    
    elif variable == 'wind_speed_10m':
        # Calm to windy
        if value < 5: return '#00aa00'  # green (calm)
        elif value < 10: return '#55dd00'  # light green
        elif value < 15: return '#ffff00'  # yellow
        elif value < 20: return '#ff9900'  # orange
        elif value < 25: return '#ff5500'  # red-orange
        else: return '#ff0000'  # red (windy)
    
    return '#888888'

def format_title(variable, value):
    """Format title based on variable"""
    titles = {
        'temperature_2m': f"Temperature: {value:.1f}°F",
        'surface_temperature': f"Surface Temperature: {value:.1f}°F",
        'precipitation': f"Precipitation: {value:.3f} in",
        'cloud_cover': f"Cloud Cover: {value:.0f}%",
        'wind_speed_10m': f"Wind Speed: {value:.1f} mph"
    }
    var_label = titles.get(variable, variable)
    return f"HRRR Forecast | Vermont & Eastern NY | {var_label}"

def add_legend(fig, ax, variable):
    """Add color scale legend to map"""
    
    legends = {
        'temperature_2m': [
            ('#0066ff', '< 0°F'),
            ('#00ccff', '0-20°F'),
            ('#00ff00', '20-32°F'),
            ('#ffff00', '32-50°F'),
            ('#ff8800', '50-70°F'),
            ('#ff4400', '70-85°F'),
            ('#ff0000', '> 85°F'),
        ],
        'precipitation': [
            ('#64b4ff', 'Trace'),
            ('#00d632', '0.01-0.1"'),
            ('#ffff00', '0.1-0.25"'),
            ('#ff8800', '0.25-0.5"'),
            ('#ff0000', '0.5-1.0"'),
            ('#8b0000', '> 1.0"'),
        ],
        'cloud_cover': [
            ('#FFD700', 'Clear (0-20%)'),
            ('#87CEEB', 'Partly Cloudy (20-50%)'),
            ('#b0b0b0', 'Mostly Cloudy (50-80%)'),
            ('#505050', 'Overcast (80-100%)'),
        ],
        'wind_speed_10m': [
            ('#00aa00', '0-5 mph'),
            ('#55dd00', '5-10 mph'),
            ('#ffff00', '10-15 mph'),
            ('#ff9900', '15-20 mph'),
            ('#ff5500', '20-25 mph'),
            ('#ff0000', '> 25 mph'),
        ],
        'surface_temperature': [
            ('#0066ff', '< 0°F'),
            ('#00ccff', '0-20°F'),
            ('#00ff00', '20-32°F'),
            ('#ffff00', '32-50°F'),
            ('#ff8800', '50-70°F'),
            ('#ff4400', '70-85°F'),
            ('#ff0000', '> 85°F'),
        ]
    }
    
    if variable in legends:
        legend_elements = [mpatches.Patch(facecolor=color, edgecolor='white', label=label, linewidth=0.5) 
                          for color, label in legends[variable]]
        legend = ax.legend(handles=legend_elements, loc='lower left', fontsize=10, 
                 title=f'{variable.replace("_", " ").title()}',
                 framealpha=0.95, facecolor='#1a1a1a', edgecolor='#00A5B3',
                 title_fontsize=11, labelcolor='white', borderpad=1)
        legend.get_frame().set_linewidth(2)

def generate_all_frames(variable='temperature_2m', num_frames=12):
    """Generate all frames for the forecast loop"""
    print(f"\n{'='*60}")
    print(f"GENERATING HRRR FORECAST LOOP WITH TERRAIN MAP")
    print(f"Variable: {variable}")
    print(f"Number of frames: {num_frames}")
    print(f"{'='*60}\n")
    
    for i in range(num_frames):
        try:
            generate_hrrr_frame(frame_index=i, variable=variable)
        except Exception as e:
            print(f"✗ Error generating frame {i}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✓ COMPLETE! Generated {num_frames} frames in 'frames/' directory")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # You can change the variable here:
    # Options: 'temperature_2m', 'precipitation', 'cloud_cover', 'wind_speed_10m', 'surface_temperature'
    
    variable_to_plot = 'temperature_2m'  # Change this to your preferred variable
    
    generate_all_frames(variable=variable_to_plot, num_frames=12)
