import os
import sys
import json
from datetime import datetime

# Базові змінні середовища mGit
MGIT_DIR = ".mgit"
SNAPSHOTS_DIR = os.path.join(MGIT_DIR, "snapshots")
INDEX_FILE = os.path.join(MGIT_DIR, "index.json")