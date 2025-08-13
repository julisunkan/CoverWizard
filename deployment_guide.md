# KDP Cover Creator - PythonAnywhere Deployment Guide

## Prerequisites

1. **PythonAnywhere Account**: Sign up for a PythonAnywhere account (free or paid)
2. **Python Version**: Ensure you're using Python 3.10 or higher

## Step-by-Step Deployment Instructions

### 1. Upload Your Code

1. Log into your PythonAnywhere dashboard
2. Go to the "Files" tab
3. Navigate to your home directory: `/home/yourusername/`
4. Create a new directory called `mysite` (or any name you prefer)
5. Upload all your project files to this directory:
   - `main.py`
   - `cover_generator.py`
   - `wsgi.py`
   - `templates/` folder with `index.html`
   - `static/` folder with CSS and create `uploads/` and `output/` subdirectories

### 2. Install Required Packages

1. Open a Bash console from your PythonAnywhere dashboard
2. Install the required packages:

```bash
pip3.10 install --user Flask==3.0.0
pip3.10 install --user Pillow==10.1.0
pip3.10 install --user reportlab==4.0.8
pip3.10 install --user Werkzeug==3.0.1
```

### 3. Configure the WSGI File

1. Edit the `wsgi.py` file in your project directory
2. Update the `project_home` path to match your actual path:
   ```python
   project_home = '/home/yourusername/mysite'  # Replace 'yourusername' with your actual username
   ```
3. Set a secure session secret:
   ```python
   os.environ['SESSION_SECRET'] = 'your-very-secure-secret-key-here'
   ```

### 4. Create Necessary Directories

In your PythonAnywhere Bash console, navigate to your project directory and create the required directories:

```bash
cd /home/yourusername/mysite
mkdir -p static/uploads
mkdir -p static/output
chmod 755 static/uploads
chmod 755 static/output
```

### 5. Set Up Web App

1. Go to the "Web" tab in your PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10
5. In the "Code" section:
   - Set "Source code" to: `/home/yourusername/mysite`
   - Set "Working directory" to: `/home/yourusername/mysite`
   - Set "WSGI configuration file" to: `/home/yourusername/mysite/wsgi.py`

### 6. Configure Static Files

In the "Static files" section, add:
- URL: `/static/`
- Directory: `/home/yourusername/mysite/static/`

### 7. Environment Variables (Optional but Recommended)

For security, you can set environment variables in the WSGI file or use PythonAnywhere's environment variable features.

### 8. Test Your Application

1. Click "Reload" on your web app configuration page
2. Visit your app at: `https://yourusername.pythonanywhere.com`

## Important Notes

### File Permissions
- Ensure the `static/uploads/` and `static/output/` directories are writable
- PythonAnywhere automatically handles most permissions, but check if you encounter issues

### Memory Limitations
- Free accounts have memory limitations
- Large image processing may timeout on free accounts
- Consider upgrading to a paid account for production use

### File Storage
- Generated covers are stored in `static/output/`
- Uploaded images are stored in `static/uploads/`
- Consider implementing cleanup routines for old files

### Debug Mode
- Disable debug mode in production by ensuring `app.debug = False` in your code
- The application currently runs with debug mode for development

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all packages are installed with `--user` flag
2. **File Not Found**: Check that all paths in `wsgi.py` are correct
3. **Permission Denied**: Ensure directories have proper write permissions
4. **Memory Errors**: Large images may cause memory issues on free accounts

### Error Logs
- Check the error log in the "Web" tab for detailed error information
- Use the "Error log" and "Server log" for debugging

## Security Considerations

1. **Secret Key**: Use a strong, unique secret key for sessions
2. **File Uploads**: The app validates file types, but consider additional security measures
3. **Rate Limiting**: Consider implementing rate limiting for production use
4. **HTTPS**: PythonAnywhere provides HTTPS by default

## Performance Optimization

1. **Image Processing**: Large images are automatically resized to optimize performance
2. **File Cleanup**: Implement periodic cleanup of old generated files
3. **Caching**: Consider implementing caching for frequently used operations

## Support

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Flask Documentation: https://flask.palletsprojects.com/
- For app-specific issues, check the error logs and ensure all dependencies are installed correctly