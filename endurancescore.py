#!/usr/bin/env python3
"""
pip3 install garminconnect garth requests readchar

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

Change API_KEY variable below to your Intervals.icu API Key

"""
import datetime
from datetime import timezone, timedelta
import json
import logging
import argparse
import os
import sys
from getpass import getpass

import readchar
import requests
from garth.exc import GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Configure debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
api = None

# Provide your Intervals.icu API key
API_KEY = "<your intervals.icu API key"


def display_json(api_call, output):
    """Format API output for better readability."""

    dashed = "-" * 20
    header = f"{dashed} {api_call} {dashed}"
    footer = "-" * len(header)

    print(header)

    if isinstance(output, (int, str, dict, list)):
        print(json.dumps(output, indent=4))
    else:
        print(output)

    print(footer)


def display_text(output):
    """Format API output for better readability."""

    dashed = "-" * 60
    header = f"{dashed}"
    footer = "-" * len(header)

    print(header)
    print(json.dumps(output, indent=4))
    print(footer)


def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        # Using Oauth1 and OAuth2 token files from directory
        print(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        )

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()
            if result1 == "needs_mfa":  # MFA is required
                mfa_code = get_mfa()
                garmin.resume_login(result2, mfa_code)

            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use.\n"
            )

            # Re-login Garmin API with tokens
            garmin.login(tokenstore)
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None

    return garmin


def get_mfa():
    """Get MFA."""

    return input("MFA one-time code: ")


def get_and_upload_endurance_scores(api, days_back=0, dry_run=False):
    today = datetime.date.today()
    current_date = today - timedelta(days=days_back)

    while current_date <= today:
        date_str = current_date.isoformat()

        try:
            data = api.get_endurance_score(date_str)
            EnduranceScore = data.get("overallScore")

            if EnduranceScore is not None:
                print(f"{date_str}: {EnduranceScore}")
                if not dry_run:
                    upload_to_intervals(date_str, EnduranceScore)
                else:
                    print("  → DRY RUN: Skipped upload")
            else:
                print(f"{date_str}: No score available")

        except Exception as e:
            print(f"{date_str}: Error fetching Garmin data - {e}")

        current_date += timedelta(days=1)


def upload_to_intervals(date_str, EnduranceScore):
    url = f"https://intervals.icu/api/v1/athlete/0/wellness/{date_str}"
    headers = {
        "accept": "*/*",
        "content-type": "application/json"
    }
    payload = {
        "EnduranceScore": EnduranceScore
    }

    try:
        response = requests.put(url, json=payload, headers=headers, auth=("API_KEY", API_KEY))
        if response.status_code in [200, 201]:
            print(f"  → Uploaded to Intervals.icu: {EnduranceScore}")
        else:
            print(f"  → Failed to upload ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"  → Error uploading to Intervals.icu: {e}")


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Upload Garmin Endurance Score to Intervals.icu")
parser.add_argument("--days", type=int, default=0, help="Number of past days to process (default: 0, only today)")
parser.add_argument("--dry-run", action="store_true", help="Only fetch data and print, do not upload")

args = parser.parse_args()

# Main program loop
while True:
    # Display header and login
    print("\n*** Get Garmin Connect Endurance Score and upload to Intervals.icu ***\n")

    # Init API
    if not api:
        api = init_api(email, password)

    if api:
        # Get endurance score(s) and optionally upload
        get_and_upload_endurance_scores(api, days_back=args.days, dry_run=args.dry_run)
        sys.exit()

    else:
        api = init_api(email, password)
