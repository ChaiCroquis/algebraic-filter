"""ground truth (fixed) for ruf013_implicit_optional — explicit Optional"""


def greet(name: str | None = None) -> str:
    return f"hello {name or 'world'}"
