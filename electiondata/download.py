import requests
import pandas as pd
import numpy as np
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


def read_wikipedia(url, contained_in_table):
    tables = pd.read_html(url)
    for t in tables:
        if contained_in_table in str(np.array(t).tolist()):
            return t
    raise RuntimeError(
        f"Could not find a table in {url} with text {contained_in_table}"
    )
