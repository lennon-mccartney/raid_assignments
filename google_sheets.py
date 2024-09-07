from __future__ import annotations

from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build


def format_cells(sheet_id: str, cell_range: str, cells: list[list[str]]) -> None:
    pass


def write_range(sheet_id: str, cell_range: str, cells = list[list[any]]) -> None:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    sheet.values().update(
        spreadsheetId=sheet_id,
        range=cell_range,
        valueInputOption='RAW',
        body={'majorDimension': 'ROWS', 'values': cells},
    ).execute()


def get_range(sheet_id: str, cell_range: str) -> list[list[Any]]:
    creds = get_credentials()
    # try:
    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=sheet_id, range=cell_range)
        .execute()
    )
    return result.get("values")


def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = "1YV8zgVa-QC0t5eEAKqoL-5u21uJkDsSOd2RC_b_KY6Y"
ROSTER_RANGE = "data_Raid!H2:R26"
