#!/bin/bash

# Create directory structure for FlipHawk
echo "Creating directory structure for FlipHawk..."

# Create static directories
mkdir -p static/css
mkdir -p static/js
mkdir -p static/images
mkdir -p static/icons

# Create templates directory
mkdir -p templates

# Move files to the right places
# CSS files should go to static/css
mv styles.css static/css/ 2>/dev/null || echo "styles.css already in static/css/"

# JS files should go to static/js
mv main.js static/js/ 2>/dev/null || echo "main.js already in static/js/"

# Convert SVG to PNG for logos
# Note: This requires ImageMagick to be installed
# If you don't have ImageMagick, you can manually convert the SVGs to PNGs
which convert >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Converting SVG logos to PNG..."
    convert -background none favicon.svg static/favicon.png 2>/dev/null || echo "Error converting favicon.svg"
    convert -background none mini-logo.svg static/mini-logo.png 2>/dev/null || echo "Error converting mini-logo.svg"
else
    echo "ImageMagick not found. Please manually convert SVG files to PNG."
fi

echo "Directory structure created successfully!"
echo "Make sure to set up your web server to serve static files from the 'static' directory."
