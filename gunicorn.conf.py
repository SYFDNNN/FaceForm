"""
gunicorn.conf.py — Gunicorn production configuration.

Loaded automatically when you run: gunicorn --config gunicorn.conf.py app:app
Override values via environment variables for flexibility.
"""

import multiprocessing
import os

# ── Binding ───────────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# ── Workers ───────────────────────────────────────────────────────────────────
# Rule of thumb for CPU-bound (ML): (2 × CPU cores) + 1
# For I/O-bound workloads you can go higher with gthread workers.
# Override with WORKERS env var.
workers = int(os.getenv("WORKERS", max(2, multiprocessing.cpu_count() * 2 + 1)))
worker_class = "gthread"  # thread-based: good for blocking ML calls
threads = int(os.getenv("THREADS", 2))

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout = int(os.getenv("TIMEOUT", 120))  # seconds before killing a worker
keepalive = 5  # seconds to keep idle connections alive
graceful_timeout = 30

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# ── Process Name ──────────────────────────────────────────────────────────────
proc_name = "face_shape_classifier"
pidfile = "/tmp/gunicorn.pid"


# ── Server Hooks ──────────────────────────────────────────────────────────────
def on_starting(server):
    server.log.info("Face Shape Classifier starting up …")


def worker_exit(server, worker):
    server.log.info("Worker %s exited", worker.pid)
