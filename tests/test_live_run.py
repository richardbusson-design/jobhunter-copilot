# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from cloud_runner import run_pipeline

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
run_pipeline(base_dir=base_dir, auto_notify=False)
