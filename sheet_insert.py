import requests
import pandas as pd
from io import BytesIO
from pymongo import MongoClient
import pymongo
import os
import certifi
import json

# ---------------------------
# MongoDB Setup (configured via env/secrets)
# ---------------------------
def get_collection() -> "pymongo.collection.Collection":
    """Return MongoDB collection using MONGO_URI and DB/COL names from env/secrets."""
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB", "audio_insights_db")
    collection_name = os.getenv("MONGO_COLLECTION", "insights")

    if not mongo_uri:
        raise RuntimeError("MONGO_URI is not set. Define it in environment variables or secrets.")

    client = MongoClient(
        mongo_uri,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=30000,
    )
    db = client[db_name]
    return db[collection_name]

# ---------------------------
# Function Definition
# ---------------------------
def download_and_insert_excel(file_url: str):
    """
    Downloads an Excel file from the given URL, parses the 'Insights' sheet, 
    and inserts it into MongoDB as a single document.
    """
    # Download file
    response = requests.get(file_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")

    # Read Excel
    excel_data = BytesIO(response.content)
    df = pd.read_excel(excel_data, sheet_name=None)  # read all sheets

    # Check for 'Insights' sheet
    if "Insights" not in df:
        raise Exception("No 'Insights' sheet found in the Excel file.")

    insights_df = df["Insights"]
    insights_list = insights_df.to_dict(orient="records")

    # Parse JSON-like strings
    for record in insights_list:
        for key, value in record.items():
            if isinstance(value, str):
                value = value.strip()
                try:
                    parsed = json.loads(value.replace("'", '"'))
                    record[key] = parsed
                except:
                    pass

    # Wrap all rows into a single document
    single_doc = {"insights": insights_list}
    collection = get_collection()
    result = collection.insert_one(single_doc)
    return f"Inserted 1 document with {len(insights_list)} rows into MongoDB."

# ---------------------------
# CLI/Module usage only (no auto-execution on import)
# ---------------------------
if __name__ == "__main__":
    file_url = "https://audiotoinsights-fastapi.onrender.com/download_excel/audio.wav"
    print(download_and_insert_excel(file_url))
