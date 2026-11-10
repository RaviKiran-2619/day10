import os
from pathlib import Path

from dotenv import load_dotenv

from pipeline_logger import PipelineLogger
from validators import validate_pan, validate_dob


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

SHEETDB_API_URL = os.getenv("SHEETDB_API_URL")

if not SHEETDB_API_URL:
    raise ValueError("SHEETDB_API_URL is missing in .env file")


# =========================================================
# FIREBASE KEY PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

FIREBASE_KEY = BASE_DIR / "firebase_key.json"


# =========================================================
# LOGGER
# =========================================================

logger = PipelineLogger(
    str(FIREBASE_KEY),
    SHEETDB_API_URL
)


# =========================================================
# VALIDATE CANDIDATE
# =========================================================

def validate_candidate(pan, dob):

    if not validate_pan(pan):
        return "fail", "INVALID_PAN"

    if not validate_dob(dob):
        return "fail", "INVALID_DOB"

    return "pass", ""


# =========================================================
# USER INPUT
# =========================================================

print("\n" + "=" * 60)
print("DAY 10 - CANDIDATE VALIDATION PIPELINE")
print("=" * 60)

candidate_id = input("Enter Candidate ID: ").strip()

pan = input("Enter PAN: ").strip().upper()

dob = input("Enter DOB (DD-MM-YYYY): ").strip()


# =========================================================
# INPUT VALIDATION
# =========================================================

if not candidate_id:
    print("❌ Candidate ID cannot be empty")
    exit()

if not pan:
    print("❌ PAN cannot be empty")
    exit()

if not dob:
    print("❌ DOB cannot be empty")
    exit()


# =========================================================
# VALIDATE
# =========================================================

status, error_type = validate_candidate(
    pan,
    dob
)


print("\n" + "-" * 60)

print(f"Candidate ID : {candidate_id}")
print(f"PAN          : {pan}")
print(f"DOB          : {dob}")
print(f"Validation   : {status.upper()}")

if error_type:
    print(f"Error Type   : {error_type}")
else:
    print("Error Type   : None")


# =========================================================
# SEND TO SHEETDB + FIRESTORE
# =========================================================

result = logger.process_record(

    candidate_id=candidate_id,

    pan=pan,

    dob=dob,

    validation_status=status,

    error_type=error_type
)


# =========================================================
# FINAL RESULT
# =========================================================

print("\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)

print(f"Candidate ID : {result['candidate_id']}")
print(f"Status       : {result['validation_status']}")
print(f"Error        : {result['error_type']}")
print(
    f"SheetDB      : "
    f"{'SUCCESS' if result['sheetdb_success'] else 'FAILED'}"
)

print("=" * 60)