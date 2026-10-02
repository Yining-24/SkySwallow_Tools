"""Exercise actual installed HTTP report endpoints using synthetic records only."""

from http.cookiejar import CookieJar
import json
from pathlib import Path
import tempfile
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

from .test_report_processing import FIXTURE, assert_summary


BASE_URL = "http://127.0.0.1:5001"


def upload(opener, endpoint, files):
    boundary = f"skyswallow-test-{uuid4().hex}"
    parts = []
    for field, filename, content in files:
        parts.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode(),
            b"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n",
            content, b"\r\n",
        ])
    parts.append(f"--{boundary}--\r\n".encode())
    request = Request(
        BASE_URL + endpoint, data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with opener.open(request, timeout=30) as response:
        assert response.status == 200
        return response.read(), response.headers


def main():
    # This is the CI-only PIN created by tests.prepare_installer_config --reset.
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    login = Request(
        BASE_URL + "/api/auth/login",
        data=json.dumps({"role": "finance", "password": "593804"}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with opener.open(login, timeout=10) as response:
        assert json.load(response)["role"] == "finance"

    temp_root = Path(tempfile.gettempdir())
    before = set(temp_root.glob("skyswallow_*"))
    fixture = FIXTURE.read_bytes()
    profit, headers = upload(opener, "/api/profit", [("file", "details.xlsx", fixture)])
    assert headers["X-Processed-Blocks"] == "1"
    for include_ck in (False, True, False):
        files = [("file", "profit.xlsx", profit)]
        if include_ck:
            files.append(("ck_file", "mapping.xlsx", fixture))
        summary, headers = upload(opener, "/api/summary", files)
        assert headers["X-Order-Count"] == "1"
        assert headers["X-Client-Count"] == "1"
        assert_summary(summary, include_ck)
        assert set(temp_root.glob("skyswallow_*")) == before, "Temporary report files were not removed."
    print("Installed Windows EXE passed profit, summary, C/K summary, repeat request, and temporary-file cleanup.")


if __name__ == "__main__":
    main()
