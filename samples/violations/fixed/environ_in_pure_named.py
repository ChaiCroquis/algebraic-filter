"""ground truth (fixed) for environ_in_pure_named — env を引数化"""


def get_config(key: str, env: dict[str, str]) -> str:
    return env.get(key, "default")
