import requests
import pandas as pd
import io

ENCODINGS = "ascii", "utf-8", "latin-1"


def download(url):
    response = requests.get(url)
    response.raise_for_status()
    data = response.content
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise RuntimeError(f"Text was not in one of our supported encodings: {ENCODINGS}")


def to_csv(s):
    return pd.read_csv(io.StringIO(s))
