"""
FlipHawk - Setup Script
This script sets up the necessary directory structure and files for FlipHawk
"""

import os
import shutil
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('setup')

def setup_directory_structure():
    """Create the necessary directory structure for FlipHawk."""
    logger.info("Setting up directory structure...")
    
    # Create directories
    directories = [
        'static',
        'static/css',
        'static/js',
        'static/images',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    return True

def copy_static_files():
    """Copy static files to their appropriate directories."""
    logger.info("Copying static files...")
    
    # List of files to copy in format (source, destination)
    files_to_copy = []
    
    # Check for favicon.png
    if os.path.exists('favicon.png'):
        files_to_copy.append(('favicon.png', 'static/favicon.png'))
    elif os.path.exists('static/favicon.png'):
        logger.info("favicon.png already in static directory")
    
    # Check for mini-logo.png
    if os.path.exists('mini-logo.png'):
        files_to_copy.append(('mini-logo.png', 'static/mini-logo.png'))
    elif os.path.exists('static/mini-logo.png'):
        logger.info("mini-logo.png already in static directory")
    
    # CSS files
    if os.path.exists('styles.css'):
        files_to_copy.append(('styles.css', 'static/css/styles.css'))
    elif os.path.exists('static/css/styles.css'):
        logger.info("styles.css already in static/css directory")
    
    # JavaScript files
    if os.path.exists('main.js'):
        files_to_copy.append(('main.js', 'static/js/main.js'))
    elif os.path.exists('static/js/main.js'):
        logger.info("main.js already in static/js directory")
    
    # Copy the files
    for source, destination in files_to_copy:
        try:
            shutil.copy2(source, destination)
            logger.info(f"Copied {source} to {destination}")
        except Exception as e:
            logger.error(f"Failed to copy {source} to {destination}: {str(e)}")
    
    return True

def check_templates():
    """Check if template files exist and copy them if needed."""
    logger.info("Checking template files...")
    
    # Check for index.html
    if os.path.exists('index.html') and not os.path.exists('templates/index.html'):
        try:
            # Copy or link the file
            shutil.copy2('index.html', 'templates/index.html')
            logger.info("Copied index.html to templates directory")
        except Exception as e:
            logger.error(f"Failed to copy index.html to templates directory: {str(e)}")
    
    # Check for scan.html
    if not os.path.exists('templates/scan.html'):
        logger.warning("scan.html not found in templates directory")
    else:
        logger.info("scan.html found in templates directory")
    
    return True

def check_python_modules():
    """Check if necessary Python modules exist."""
    logger.info("Checking Python modules...")
    
    # List of required modules
    required_modules = [
        'app.py',
        'scraper_manager.py',
        'comprehensive_keywords.py'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        if not os.path.exists(module):
            missing_modules.append(module)
    
    if missing_modules:
        logger.warning(f"Missing Python modules: {', '.join(missing_modules)}")
        return False
    else:
        logger.info("All required Python modules found")
        return True

def main():
    """Main setup function."""
    logger.info("Starting FlipHawk setup...")
    
    # Setup directory structure
    setup_directory_structure()
    
    # Copy static files
    copy_static_files()
    
    # Check templates
    check_templates()
    
    # Check Python modules
    check_python_modules()
    
    logger.info("FlipHawk setup completed!")
    logger.info("You can now run the application with: python app.py")

if __name__ == "__main__":
    main()
