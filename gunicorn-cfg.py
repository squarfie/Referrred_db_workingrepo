# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

bind = '0.0.0.0:80'  # Bind to all interfaces on port 80 for production
workers = 3  # Adjust based on CPU general rule is (2 * number of CPU cores) + 1.
accesslog = '/var/log/gunicorn/access.log'  # Log access to a file
loglevel = 'info'  # Use 'info' or 'warning' for production
capture_output = True
enable_stdio_inheritance = True
