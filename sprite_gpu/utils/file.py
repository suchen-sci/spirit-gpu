import os
import tempfile
from urllib.parse import urlparse
import backoff
import requests
from email import message_from_string


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def download_file_from_url(url: str) -> str:
    """
    Download a file from a URL and save it to temporary directory.
    """
    with requests.get(url, stream=True, timeout=5) as response:
        response.raise_for_status()

        file_extension = ""

        content_disposition = response.headers.get("Content-Disposition", "")
        if content_disposition != "":
            msg = message_from_string(f"Content-Disposition: {content_disposition}")
            file_extension = os.path.splitext(msg.get("filename", ""))[1]

        if not file_extension:
            file_extension = os.path.splitext(urlparse(url).path)[1]

        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            for chunk in response.iter_content(1024 * 1024 * 10):
                if chunk:
                    temp_file.write(chunk)
            return temp_file.name
