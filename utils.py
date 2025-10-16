from urllib.parse import unquote


def clean_text(value):
    """Decode unicode escapes and URL encodings in a string."""
    if not isinstance(value, str):
        return value
    try:
        value = unquote(value)
        value = value.replace("_", " ")
        return value
    except Exception as e:
        print(f"Error cleaning data: {e}")
        return value


def clean_data(obj):
    """Recursively clean data in a nested structure."""
    if isinstance(obj, dict):
        return {k: clean_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_data(item) for item in obj]
    elif isinstance(obj, str):
        return clean_text(obj)
    else:
        return obj
