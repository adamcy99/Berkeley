from typing import Dict
from urllib.parse import parse_qs, urlencode, urljoin

from dash import get_relative_path


def build_url(path: str, **kwargs) -> str:
    """
    builds a url with key=value pairs, ex:

    >>> build_url('/foo/bar', red=1, dog=['poodle', 'chihuahua'])
    '/foo/bar?red=1&dog=poodle&dog=chihuahua'
    """
    query = "?" + urlencode(kwargs, doseq=True)
    return urljoin(get_relative_path(path), query)


def extract_url_parameters(url: str) -> Dict[str, str]:
    """
    Extracts variable parameters from a URL returning a dict.

    url:  http://foo.com/bar?red=1&dog=poodle&dog=chihuahua
    returns:  {
        'red': '1',   # the string 1, not the number
        'dog': ['poodle', 'chihuahua']
    }
    """
    params: dict = parse_qs((url or "").strip("?"))
    return {
        k: v[0] if len(v) < 2 else v
        for k, v in params.items()
    }
