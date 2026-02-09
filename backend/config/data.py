import os
from backend.config import get_settings

settings = get_settings()

DATA_OUT_PATH = os.path.join(settings.backend_root, 'data')