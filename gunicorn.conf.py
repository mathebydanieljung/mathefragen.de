import multiprocessing

import os

# Bind to PORT if defined, otherwise default to 8000
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count()
timeout = 120  # Adjust the timeout as needed
# recycle workers so memory bloated by heavy requests is returned to the OS
max_requests = 1000
max_requests_jitter = 100
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
accesslog = '-'  # log to stdout
errorlog = '-'  # log to stdout
