#!/usr/bin/env python3
"""
pip3 install garminconnect garth requests readchar

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""

import datetime
from datetime import timezone, timedelta
import json
import logging
import argparse
import os
import sys
import base64
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
tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garminconnect")
api = None

# API Key handling
API_KEY = None
API_KEY_FILE = os.path.join(tokenstore, "api_key.json")


def get_api_key(force_new=False):
    """Load stored API key, or prompt for it if not available or forced"""
    if not force_new and os.path.exists(API_KEY_FILE):
        try:
            with open(API_KEY_FILE, "r") as f:
                encoded = json.load(f).get("api_key", "")
                if encoded:
                    return base64.b64decode(encoded.encode()).decode()
        except Exception as e:
            logger.warning(f"Error reading stored API key: {e}")

    # Ask user to enter a new API key
    key = input("Enter your Intervals.icu API Key: ").strip()

    # Store encoded key
    try:
        os.makedirs(os.path.dirname(API_KEY_FILE), exist_ok=True)
        with open(API_KEY_FILE, "w") as f:
            json.dump({"api_key": base64.b64encode(key.encode()).decode()}, f)
        print(f"API key saved to {API_KEY_FILE}")
    except Exception as e:
        logger.error(f"Failed to save API key: {e}")

    return key


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
            # Re-login Garmin API with tokens
            print(f"Oauth tokens stored in '{tokenstore}' for future use.\n")
            garmin.login(tokenstore)

        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None
    
    print(
        f"Login to Garmin Connect succesful.\n"
    )
    

    return garmin


def get_mfa():
    """Get MFA."""

    return input("MFA one-time code: ")


def get_and_upload_endurance_scores(api, days_back=0, dry_run=False):
    today = datetime.date.today()
    current_date = today - timedelta(days=days_back)
    start_date = current_date

    while current_date <= today:
        date_str = current_date.isoformat()

        try:
            data = api.get_endurance_score(date_str)
            EnduranceScore = data.get("overallScore")

            if EnduranceScore is not None:
                if current_date == start_date:
                    print(f"Endurance score data from Intervals.icu:")
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
    global API_KEY
    url = f"https://intervals.icu/api/v1/athlete/0/wellness/{date_str}"
    headers = {
        "accept": "*/*",
        "content-type": "application/json"
    }
    payload = {
        "EnduranceScore": EnduranceScore
    }

    def try_upload(api_key):
        return requests.put(url, json=payload, headers=headers, auth=("API_KEY", api_key))

    try:
        response = try_upload(API_KEY)
        if response.status_code in [200, 201]:
            print(f"\n  → Uploaded to Intervals.icu: {EnduranceScore}")
        elif response.status_code == 401:
            print(f"  → Unauthorized: Your API key may be invalid.")
            API_KEY = get_api_key(force_new=True)
            response = try_upload(API_KEY)
            if response.status_code in [200, 201]:
                print(f"  → Uploaded with new API key: {EnduranceScore}")
            else:
                print(f"  → Failed again ({response.status_code}): {response.text}")
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
        API_KEY = get_api_key()
        get_and_upload_endurance_scores(api, days_back=args.days, dry_run=args.dry_run)
        sys.exit()

    else:
        api = init_api(email, password)
