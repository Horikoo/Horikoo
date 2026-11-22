#!/usr/bin/env python3
"""
Run this ONCE on your own computer to connect your YouTube channel.

  pip install google-auth-oauthlib
  python get_youtube_token.py client_secret.json

A browser opens -> log in with the Google account that owns the channel -> allow.
It then prints the 3 values to save as GitHub secrets:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""

import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python get_youtube_token.py client_secret.json")
        return 1
    flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    info = json.load(open(sys.argv[1]))
    info = info.get("installed") or info.get("web")
    print("\n=== GitHub > Settings > Secrets and variables > Actions > New repository secret ===")
    print(f"YT_CLIENT_ID      = {info['client_id']}")
    print(f"YT_CLIENT_SECRET  = {info['client_secret']}")
    print(f"YT_REFRESH_TOKEN  = {creds.refresh_token}")
    print("\nKeep these private. Do not share them or put them in any file in the repository.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
