# Deployment Guide - Render.com

This guide explains how to deploy the Headshot Generator to Render.com using Docker.

## Prerequisites

- A GitHub repository with your code
- A Render.com account (free tier available)
- Docker installed locally for testing (optional)

## Deployment Methods

### Method 1: Automatic Deployment (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add deployment configuration for Render.com"
   git push origin main
   ```

2. **Connect to Render.com**:
   - Go to [render.com](https://render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing your headshot generator
   - Render will automatically detect the `render.yaml` file

3. **Deploy**:
   - Render will automatically build and deploy using the Dockerfile
   - The application will be available at `https://your-app-name.onrender.com`

### Method 2: Manual Service Creation

1. **Create New Web Service**:
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**:
   - **Name**: `headshot-generator`
   - **Environment**: Docker
   - **Region**: Choose your preferred region
   - **Branch**: `main`
   - **Dockerfile Path**: `./Dockerfile`

3. **Environment Variables** (set in Render dashboard):
   ```
   STREAMLIT_SERVER_HEADLESS=true
   STREAMLIT_SERVER_PORT=10000
   STREAMLIT_SERVER_ADDRESS=0.0.0.0
   STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
   STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10
   ```

4. **Deploy**: Click "Create Web Service"

## Local Testing

Test the Docker build locally before deploying:

```bash
# Build the Docker image
docker build -t headshot-generator .

# Run locally
docker run -p 10000:10000 headshot-generator

# Test in browser
open http://localhost:10000
```

## Configuration Files

- **Dockerfile**: Multi-stage build optimized for Streamlit
- **render.yaml**: Render service configuration
- **.dockerignore**: Optimizes build context
- **start.sh**: Optional startup script
- **.streamlit/config.toml**: Streamlit configuration for production

## Features Optimized for Cloud Deployment

- **Port Configuration**: Uses port 10000 (Render.com standard)
- **Upload Limits**: 10MB max file size for images
- **Health Checks**: Automatic health monitoring
- **Logging**: Structured logging for troubleshooting
- **Security**: CORS and XSRF protection disabled for cloud deployment
- **Performance**: Optimized Python dependencies and caching

## Monitoring and Troubleshooting

1. **View Logs**: 
   - Go to Render Dashboard → Your Service → Logs
   - Logs show application startup and any errors

2. **Health Check**:
   - Render automatically monitors `/_stcore/health`
   - Service will restart if health check fails

3. **Common Issues**:
   - **Build failures**: Check Dockerfile syntax and dependencies
   - **Port issues**: Ensure port 10000 is used consistently
   - **File upload issues**: Check file size limits
   - **Memory issues**: Consider upgrading to paid plan for more resources

## Upgrading

To upgrade from free to paid plan:
1. Go to Service Settings in Render Dashboard
2. Change plan from "Starter" to "Standard" or higher
3. Benefits: More CPU, RAM, and no sleep mode

## Custom Domain

To use a custom domain:
1. Go to Service Settings → Custom Domains
2. Add your domain (requires paid plan)
3. Configure DNS records as instructed

## Cost Optimization

**Free Tier Limitations**:
- Service sleeps after 15 minutes of inactivity
- 750 hours per month (sufficient for personal use)
- Limited resources

**Paid Tier Benefits**:
- No sleep mode
- More CPU and memory
- Custom domains
- Priority support

## Security Notes

- The application runs in a containerized environment
- File uploads are processed in memory and not stored permanently
- No persistent data storage (stateless application)
- Consider adding authentication for production use

## Support

For deployment issues:
- Check Render.com documentation
- Review application logs in Render Dashboard
- Verify all configuration files are present and correct