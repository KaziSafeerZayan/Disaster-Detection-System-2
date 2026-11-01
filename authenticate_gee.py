"""One-time, user-controlled Google Earth Engine sign-in and project check."""
import argparse
import os

import ee
import httplib2

from config import GEE_PROJECT_ID


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=os.getenv("GEE_PROJECT_ID") or GEE_PROJECT_ID)
    args = parser.parse_args()
    print(f"Earth Engine project: {args.project}")
    print("Complete the Google sign-in in your browser. The dashboard does not handle your password.")
    try:
        ee.Authenticate(auth_mode="localhost")
        ee.Initialize(project=args.project, http_transport=httplib2.Http(timeout=15))
        ee.Number(1).getInfo()
    except Exception as exc:
        print(f"\nRadar setup could not finish: {exc}")
        print("Your Google account needs access to an Earth Engine-enabled Cloud project.")
        print("Setup guide: https://developers.google.com/earth-engine/guides/auth")
        return 1
    print("\nEarth Engine is connected. Reload the dashboard to load radar imagery.")
    if args.project != (os.getenv("GEE_PROJECT_ID") or GEE_PROJECT_ID):
        print(f"Before starting the dashboard with this project, set GEE_PROJECT_ID={args.project}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
