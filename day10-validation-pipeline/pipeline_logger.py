import requests
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore


class PipelineLogger:

    def __init__(self, service_account_path, sheetdb_api_url):

        # -----------------------------------------------------
        # Store SheetDB API URL
        # -----------------------------------------------------

        self.sheetdb_api_url = sheetdb_api_url

        # -----------------------------------------------------
        # Firebase Initialization
        # -----------------------------------------------------

        try:

            cred = credentials.Certificate(
                service_account_path
            )

            if not firebase_admin._apps:

                firebase_admin.initialize_app(cred)

            self.db = firestore.client()

            print(" Firebase initialized successfully")

        except Exception as e:

            print(" Firebase initialization failed")
            print("Error:", str(e))

            raise


    # =========================================================
    # SHEETDB - CHECK DUPLICATE
    # =========================================================

    def candidate_exists(self, candidate_id):

        try:

            response = requests.get(
                self.sheetdb_api_url,
                params={
                    "candidate_id": candidate_id
                },
                timeout=15
            )

            print(
                "Duplicate Check Status:",
                response.status_code
            )

            if response.status_code != 200:

                return False

            data = response.json()

            if isinstance(data, list):

                for record in data:

                    if str(
                        record.get("candidate_id", "")
                    ).strip().upper() == candidate_id.upper():

                        return True

            return False

        except Exception as e:

            print(
                " Duplicate check failed:",
                str(e)
            )

            return False


    # =========================================================
    # SHEETDB - APPEND DATA
    # =========================================================

    def append_to_sheetdb(self, data):

        try:

            candidate_id = data.get(
                "candidate_id",
                ""
            )

            # -------------------------------------------------
            # Duplicate Check
            # -------------------------------------------------

            if self.candidate_exists(candidate_id):

                print(
                    f" DUPLICATE FOUND: {candidate_id}"
                )

                print(
                    " Data was NOT added to SheetDB"
                )

                return False, "DUPLICATE_CANDIDATE"


            # -------------------------------------------------
            # Add new record to SheetDB
            # -------------------------------------------------

            response = requests.post(

                self.sheetdb_api_url,

                json={
                    "data": data
                },

                timeout=15
            )

            print(
                "SheetDB Status:",
                response.status_code
            )

            print(
                "SheetDB Response:",
                response.text
            )


            # -------------------------------------------------
            # Successful response
            # -------------------------------------------------

            if response.status_code in [200, 201]:

                try:

                    result = response.json()

                except Exception:

                    result = {}


                print(
                    " SheetDB data added successfully"
                )

                return True, result


            # -------------------------------------------------
            # Failed response
            # -------------------------------------------------

            print(
                " SheetDB data insertion failed"
            )

            return False, response.text


        except requests.exceptions.RequestException as e:

            print(
                " SheetDB Request Error:",
                str(e)
            )

            return False, str(e)


        except Exception as e:

            print(
                " SheetDB Unexpected Error:",
                str(e)
            )

            return False, str(e)


    # =========================================================
    # FIRESTORE - WRITE AUDIT LOG
    # =========================================================

    def write_audit_log(
        self,
        candidate_id,
        source_field,
        validation_status,
        error_type,
        sheetdb_row_id
    ):

        try:

            # -------------------------------------------------
            # Audit data
            # -------------------------------------------------

            log_data = {

                "candidate_id": candidate_id,

                "source_field": source_field,

                "validation_status": validation_status,

                "error_type": error_type,

                "sheetdb_row_id": sheetdb_row_id,

                "timestamp": datetime.now(
                    timezone.utc
                )
            }


            print(
                "\n Writing audit log to Firestore..."
            )


            # -------------------------------------------------
            # validation_logs collection
            # -------------------------------------------------

            collection_ref = self.db.collection(
                "validation_logs"
            )


            # -------------------------------------------------
            # Create new Firestore document
            # -------------------------------------------------

            document_ref = collection_ref.document()

            document_ref.set(log_data)


            print(
                " FIRESTORE DATA ADDED"
            )

            print(
                "Document ID:",
                document_ref.id
            )

            print(
                "Candidate:",
                candidate_id
            )


            return True


        except Exception as e:

            print(
                "\n FIRESTORE ERROR"
            )

            print(
                "Error Type:",
                type(e).__name__
            )

            print(
                "Error Message:",
                str(e)
            )


            return False


    # =========================================================
    # COMPLETE PIPELINE
    # =========================================================

    def process_record(
        self,
        candidate_id,
        pan,
        dob,
        validation_status,
        error_type
    ):

        print("\n")
        print("=" * 60)

        print(
            f"PROCESSING CANDIDATE: {candidate_id}"
        )

        print("=" * 60)


        # -----------------------------------------------------
        # Prepare SheetDB row
        # -----------------------------------------------------

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()


        row_data = {

            "candidate_id": candidate_id,

            "source_field": "PAN,DOB",

            "validation_status": validation_status,

            "error_type": error_type,

            "sheetdb_row_id": candidate_id,

            "timestamp": timestamp
        }


        # -----------------------------------------------------
        # STEP 1 - SheetDB
        # -----------------------------------------------------

        print(
            "\n STEP 1: SheetDB"
        )


        sheetdb_success, sheetdb_response = (
            self.append_to_sheetdb(row_data)
        )


        # -----------------------------------------------------
        # Final status
        # -----------------------------------------------------

        final_status = validation_status

        final_error = error_type


        # -----------------------------------------------------
        # SheetDB failed
        # -----------------------------------------------------

        if not sheetdb_success:

            # Duplicate is a separate condition

            if sheetdb_response == "DUPLICATE_CANDIDATE":

                final_status = "fail"

                final_error = "DUPLICATE_CANDIDATE"


            elif final_error == "":

                final_status = "fail"

                final_error = "SHEETDB_ERROR"


        # -----------------------------------------------------
        # STEP 2 - Firestore
        # -----------------------------------------------------

        print(
            "\n STEP 2: Firestore Audit Logging"
        )


        firebase_success = self.write_audit_log(

            candidate_id=candidate_id,

            source_field="PAN,DOB",

            validation_status=final_status,

            error_type=final_error,

            sheetdb_row_id=candidate_id
        )


        # -----------------------------------------------------
        # Final console result
        # -----------------------------------------------------

        print("\n")
        print("-" * 60)

        print(
            f"Candidate ID : {candidate_id}"
        )

        print(
            f"Validation   : {final_status}"
        )

        print(
            f"Error Type   : {final_error}"
        )

        print(
            "SheetDB      :",
            "SUCCESS"
            if sheetdb_success
            else "FAILED"
        )

        print(
            "Firebase     :",
            "SUCCESS"
            if firebase_success
            else "FAILED"
        )

        print("-" * 60)


        # -----------------------------------------------------
        # RETURN RESULT
        # -----------------------------------------------------

        return {

            "candidate_id": candidate_id,

            "validation_status": final_status,

            "error_type": final_error,

            "sheetdb_success": sheetdb_success,

            "firebase_success": firebase_success
        }