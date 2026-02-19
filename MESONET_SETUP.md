# VTSU Mesonet Continuous Updates Setup

This guide explains how to set up automatic mesonet data updates using GitHub Actions so your weather data updates even when your computer is off.

## How It Works

1. **GitHub Actions Workflow**: A scheduled workflow runs every 5 minutes and fetches the latest weather data from the Synoptic API
2. **Data Storage**: The weather data is stored in `mesonet-data.json` in your repository
3. **Web Display**: Your index.html now fetches data from this JSON file instead of directly calling the API
4. **Always Available**: The data is always fresh and accessible, regardless of your computer's status

## Setup Instructions

### Step 1: Push Your Code to GitHub

If you haven't already, push your code to a GitHub repository:

```bash
git init
git add .
git commit -m "Initial commit with mesonet updates"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Step 2: Configure GitHub Secrets

You need to add your Synoptic API token as a GitHub secret:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name it: `SYNOPTIC_TOKEN`
5. Paste your Synoptic API token: `a5d9d976cd324d9e9b2c61fbc55b8b61` (or your own token)
6. Click **Add secret**

### Step 3: Enable GitHub Actions

1. Go to your repository's **Actions** tab
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. You should see the "Update VTSU Mesonet Data" workflow listed

### Step 4: Test the Workflow

1. Go to **Actions** → **Update VTSU Mesonet Data**
2. Click **Run workflow** → **Run workflow** button
3. Wait for it to complete (should take ~10 seconds)
4. Check the `mesonet-data.json` file in your repository - it should now contain live weather data

## How to Deploy Your Changes

Once you've set up the workflow:

1. Commit and push your HTML and Flask changes:
   ```bash
   git add .
   git commit -m "Update mesonet to use persistent cloud data"
   git push
   ```

2. Make sure your Flask app is running and has access to the `.github/workflows` setup (it's already configured in `app.py`)

## Workflow Schedule

The workflow runs:
- **Every 5 minutes** (configurable in `.github/workflows/update-mesonet-data.yml`)
- **On manual trigger** (you can manually run it anytime from the Actions tab)

## To Change Update Frequency

Edit `.github/workflows/update-mesonet-data.yml` and change the cron schedule:

```yaml
on:
  schedule:
    # Change the cron expression below (format: minute hour day month day-of-week)
    - cron: '*/5 * * * *'  # Every 5 minutes
    # Examples:
    # - cron: '*/10 * * * *'  # Every 10 minutes  
    # - cron: '0 * * * *'     # Every hour
    # - cron: '*/15 * * * *'  # Every 15 minutes
```

Then push the changes:
```bash
git add .github/workflows/update-mesonet-data.yml
git commit -m "Update mesonet workflow schedule"
git push
```

## Monitoring the Workflow

- Check the **Actions** tab to see workflow history
- Look for the `mesonet-data.json` file in your repository - it will show when it was last updated
- If the workflow fails, GitHub sends email notifications (configurable in your GitHub settings)

## Troubleshooting

### Workflow not running?
- Make sure GitHub Actions is enabled in repository settings
- Check that `SYNOPTIC_TOKEN` secret is configured
- Verify the workflow file syntax (.yml formatting)

### Data not updating?
- Check the Actions tab for error messages
- Verify your Synoptic API token is valid
- Check network connectivity (GitHub Actions runs on GitHub's servers)

### Data showing as "pending"?
- The workflow hasn't run yet - click **Run workflow** manually
- Or wait for the next scheduled run (5-minute intervals)

## File References

- `.github/workflows/update-mesonet-data.yml` - The workflow definition
- `mesonet-data.json` - Stored weather data (auto-updated)
- `index.html` - Updated to fetch from the stored data
- `app.py` - Flask route to serve the mesonet data

## Support

Questions? Check the GitHub Actions documentation:
https://docs.github.com/en/actions
