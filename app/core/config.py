# app/core/config.py
import os
from dynaconf import Dynaconf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

settings = Dynaconf(
    root_path=BASE_DIR,
    settings_files=["settings.toml", ".secrets.toml"],
    environments=True,
    env_switcher="ENV_FOR_DYNACONF",
    load_dotenv=True,
    merge_enabled=True,
    env="development",
)
