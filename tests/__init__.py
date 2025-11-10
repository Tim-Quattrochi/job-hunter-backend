"""Test package configuration for the Job Hunter backend."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
