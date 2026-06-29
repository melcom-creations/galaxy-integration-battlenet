import os
import sys

# Add the bundled Modules directory to sys.path so local dependencies can be imported.
modules_dir = os.path.join(os.path.dirname(__file__), 'Modules')
if os.path.isdir(modules_dir) and modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)