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
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

warnings.filterwarnings('ignore')

# Create frames directory if it doesn't exist
os.makedirs('frames', exist_ok=True)

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

def generate_hrrr_frame(frame_index=0, variable='temperature_2m'):
    """
    Generate a single HRRR forecast frame for VT & Eastern NY
    
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
    ) with cartopy projection
    fig = plt.figure(figsize=(14, 10), facecolor='#1a1a1a')
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent (Vermont and Eastern NY region)
    ax.set_extent([-76.5, -70.5, 42.0, 45.5], crs=ccrs.PlateCarree())
    
    # Add topographic/terrain background
    ax.stock_img()
    
    # Add geographic features
    # States
    states = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none',
        edgecolor='white',
        linewidth=2
    )
    ax.add_feature(states, zorder=2)
    
    # Coastlines
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=1.5, edgecolor='white', zorder=2)
    
    # Lakes
    ax.add_feature(cfeature.LAKES.with_scale('50m'), alpha=0.5, facecolor='lightblue', 
                   edgecolor='white', linewidth=0.5, zorder=1)
    
    # Rivers
    ax.add_feature(cfeature.RIVERS.with_scale('50m'), edgecolor='cyan', linewidth=0.5, 
                   alpha=0.6, zorder=1)
    
    # Borders
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=1, edgecolor='white', 
                   linestyle='--', alpha=0.7, zorder=2)
    
    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, 
                      linestyle='--', zorder=3)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 10, 'color': 'white'}
    gl.ylabel_style = {'size': 10, 'color': 'white'}
    
    # Plot center observation point
    lat, lon = response.Latitude(), response.Longitude()
    color = get_color_for_value(value, variable)
    
    ax.scatter(lon, lat, s=800, color=color, edgecolors='white', linewidth=3, 
               zorder=5, marker='o', label='VTSU Lyndon', transform=ccrs.PlateCarree())
    
    # Add state/region labels
    ax.text(-72.7, 44.0, 'VERMONT', fontsize=16, weight='bold', 
            color='white', alpha=0.9, ha='center', 
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.6),
            transform=ccrs.PlateCarree(), zorder=4)
    ax.text(-75.0, 43.0, 'NEW YORK', fontsize=14, weight='bold', 
            color='white', alpha=0.9, ha='center',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.6),
            transform=ccrs.PlateCarree(), zorder=4)
    ax.text(-71.5, 43.5, 'NH', fontsize=12, weight='bold', 
            color='white', alpha=0.9, ha='center',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.6),
            transform=ccrs.PlateCarree(), zorder=4 weight='bold', 
            color='white', alpha=0.6, ha='center')
    ax.text(-71.5, 43, 'NH', fontsize=12, weight='bold', 
            color='white', alpha=0.6, ha='center')
    
    # Add location annotation
    ax.annotate(f'VTSU Lyndon\n({lat:.2f}°N, {lon:.2f}°W)', 
                xy=(lon, lat), xytext=(lon-0.8, lat+0.5),
                fontsize=11, weight='bold', color='white',
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.8, edgecolor='white'),
                arrowprops=dict(arrowstyle='->', color='white', lw=2),
                transform=ccrs.PlateCarree(), zorder=6)
    
    # Add data value box
    title_text = format_title(variable, value)
    fig.suptitle(title_text, fontsize=18, weight='bold', color='#00A5B3', y=0.98)
    
    # Add valid time and forecast hour
    time_text = f"Valid: {current_time.strftime('%a %b %d, %Y - %H:%M %Z')} | Forecast Hour +{frame_index:02d}"
    ax.text(0.5, 0.01, time_text, transform=ax.transAxes, 
            fontsize=12, color='white', ha='center', va='bottom', weight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.8, edgecolor='#00A5B3', linewidth=2))
    
    # Add legend
    add_legend(fig, ax, variable)
    
    # Add branding
    ax.text(0.01, 0.01, 'Vermont State University | Weather Center', 
            transform=ax.transAxes, fontsize=10, color='white', 
            ha='left', va='bottom', alpha=0.7, style='italic')
    
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
        legend_elements = [mpatches.Patch(facecolor=color, edgecolor='white', label=label) 
                          for color, label in legends[variable]]
        ax.legend(handles=legend_elements, loc='lower left', fontsize=10, 
                 title=f'{variable.replace("_", " ").title()}',
                 framealpha=0.95, facecolor='#1a1a1a', edgecolor='#00A5B3',
                 title_fontsize=11, labelcolor='white')

def generate_all_frames(variable='temperature_2m', num_frames=12):
    """Generate all frames for the forecast loop"""
    print(f"\n{'='*60}")
    print(f"GENERATING HRRR FORECAST LOOP")
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
