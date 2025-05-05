# FlipHawk Deployment Guide

This guide provides step-by-step instructions for deploying FlipHawk to Render.com.

## Prerequisites

Before deploying, ensure you have:

1. A GitHub repository with your FlipHawk code
2. A Render.com account
3. The following files in your repository:
   - app.py
   - requirements.txt
   - render.yaml (optional, but recommended)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository has the correct directory structure:

```
fliphawk/
├── app.py                  # Main application file
├── scraper_manager.py      # Scraper manager implementation 
├── comprehensive_keywords.py # Keywords database
├── static/                 # Static files directory
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── main.js
│   ├── favicon.png
│   └── mini-logo.png
├── templates/              # HTML templates
│   ├── index.html
│   └── scan.html
├── requirements.txt        # Python dependencies
└── render.yaml             # Render configuration
```

### 2. Deploy to Render

#### Option 1: Deploy using the Render Dashboard

1. Log in to your Render account
2. Click "New" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: fliphawk (or your preferred name)
   - **Environment**: Python
   - **Region**: Choose the region closest to your users
   - **Branch**: main (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

5. Click "Create Web Service"

#### Option 2: Deploy using render.yaml (Blueprint)

1. Ensure you have a render.yaml file in your repository
2. Log in to your Render account
3. Click "New" and select "Blueprint"
4. Connect your GitHub repository
5. Review the resources defined in your render.yaml
6. Click "Apply"

### 3. Environment Variables

Set the following environment variables in your Render dashboard:

- `PORT`: 8000 (or your preferred port)
- `PYTHON_VERSION`: 3.11.0 (or your preferred version)
- `FLASK_ENV`: production

### 4. Verify Deployment

After deployment is complete:

1. Visit your Render service URL (e.g., https://fliphawk.onrender.com)
2. Check the API health endpoint: https://fliphawk.onrender.com/api/health
3. Test the scan functionality: https://fliphawk.onrender.com/scan

### Troubleshooting

If you encounter issues:

1. Check the Render logs for error messages
2. Ensure all required directories exist
3. Verify that your dependencies are correctly specified in requirements.txt
4. Make sure the PORT environment variable matches the port in your app.py

Common errors:

- **404 Not Found**: Check that your routes are correctly defined in app.py
- **500 Internal Server Error**: Check application logs for Python errors
- **Module not found**: Ensure all required modules are in requirements.txt

### Updating Your Deployment

To update your deployment:

1. Push changes to your GitHub repository
2. Render will automatically rebuild and redeploy your application

For manual updates:
1. Go to your Web Service in the Render dashboard
2. Click the "Manual Deploy" button
3. Select "Clear build cache & deploy"

## Support

If you need assistance with your deployment, please contact support@fliphawk.org
