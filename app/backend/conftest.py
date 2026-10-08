"""
conftest.py de pytest.
"""

import sys
import os

# Agrega la carpeta app al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
