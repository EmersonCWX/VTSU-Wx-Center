# VTSU Lyndon Weather Center

A real-time weather information portal for Vermont State University Lyndon featuring live local radar, weather model forecasts, and mesonet data.

## Features

- **Live KCXX Radar**: Real-time radar loop from the National Weather Service Burlington radar
- **GFS Model**: 15-day precipitation and MSLP forecasts via TropicalTidbits
- **ECMWF Model**: European model forecasts via TropicalTidbits
- **HRRR Model**: High-resolution rapid refresh via PivotalWeather
- **VTSU Mesonet**: Local weather station data from Northern Vermont Atmospheric Institute

## Setup & Deployment

### Local Testing
Simply open `index.html` in a web browser.

### GitHub Pages Deployment

1. Create a GitHub repository for this project
2. Push files to the main branch:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```
3. Enable GitHub Pages in repository settings:
   - Go to **Settings > Pages**
   - Select **Source: Deploy from a branch**
   - Select **main** branch and **/(root)** folder
   - Click **Save**

4. Your site will be available at `https://<username>.github.io/<repo-name>` (or `https://<username>.github.io` if the repo is named `<username>.github.io`)

5. **Update URLs** in `_config.yml`:
   ```yaml
   url: "https://<username>.github.io"
   baseurl: "/<repo-name>"  # Omit if using user/org site repo
   ```

### File Structure

```
.
├── index.html           # Main splash page (rename from VTSU Wx Center Splash.html)
├── _config.yml         # Jekyll configuration for GitHub Pages
├── .nojekyll           # Disables Jekyll processing (optional)
├── README.md           # This file
└── assets/             # (Optional) For images, CSS, JS if separated
```

## Weather Data Sources

- **NWS KCXX Radar**: https://radar.weather.gov/ridge/standard/KCXX_loop.gif
- **TropicalTidbits GFS/ECMWF**: https://www.tropicaltidbits.com/analysis/models/
- **PivotalWeather HRRR**: https://www.pivotalweather.com/
- **VTSU Mesonet**: https://atmos.northernvermont.edu/weather-data/weather-station/

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled for clock and external link functionality

## Credits

Coded by Emerson Charles (she/her)

## Contact

For questions or assistance: dxc00407@vsc.edu
