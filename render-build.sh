#!/usr/bin/env bash
set -o errexit

# Install system dependencies for Pillow
apt-get update
apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    libwebp-dev

# Install Python dependencies
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate