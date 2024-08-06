import time
import subprocess
from sprite_gpu.settings import EASE_TEST_MODE

from .validate import *
from .file import *


def current_unix_milli():
    return round(time.time() * 1000)


def is_cuda_available() -> bool:
    try:
        output = subprocess.check_output("nvidia-smi", shell=True).decode()
        if "NVIDIA-SMI" in output:
            return True
    except Exception:
        pass
    return False


def is_test_mode():
    """
    Check if the application is running in test mode.
    In test mode, application will run as a local server.
    """
    mode = os.environ.get(EASE_TEST_MODE)
    if mode is None:
        return False
    if mode in [
        "True",
        "true",
        "1",
        "yes",
        "y",
    ]:
        return True
    return False
