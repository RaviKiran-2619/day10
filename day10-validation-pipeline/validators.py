import re
from datetime import datetime


def validate_pan(pan):
    """
    Validates Indian PAN format.

    Expected:
    ABCDE1234F
    """

    if not pan:
        return False

    pan = str(pan).strip().upper()

    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"

    return bool(re.fullmatch(pattern, pan))


def validate_dob(dob):
    pattern = r"^\d{2}-\d{2}-\d{4}$"
    return bool(re.fullmatch(pattern, dob))

    

def validate_candidate(candidate):
    """
    Validates PAN and DOB.

    Returns:
        valid
        errors
    """

    errors = []

    pan = candidate.get("pan")
    dob = candidate.get("dob")

    if not validate_pan(pan):
        errors.append("INVALID_PAN")

    if not validate_dob(dob):
        errors.append("INVALID_DOB")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }