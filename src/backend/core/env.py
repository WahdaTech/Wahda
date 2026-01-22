__all__ = ["get_env"]

import os


def get_env(var_name: str, default: str) -> str:
    env_prefix = "WD"
    return os.environ.get(f"{env_prefix}_{var_name}", default)
