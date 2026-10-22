"""Stands in for Beyond Compare in tests/measure_footprint.py: the compare stays open until the tool is killed."""

import signal
import sys
import time

signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
while True:
    time.sleep(60)
