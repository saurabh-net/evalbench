import os
import zipfile
import logging
import sys
import tempfile
from reporting.report import Reporter, STORETYPE
from google.cloud import storage
import pandas as pd

class GcsReporter(Reporter):
    def __init__(self, reporting_config, job_id, run_time):
        super().__init__(reporting_config, job_id, run_time)
        self.bucket_name = reporting_config.get("bucket")
        self.client = storage.Client()
        
        # If running via eval_server.py (gRPC), force path prefix
        if sys.argv[0].endswith("eval_server.py"):
            self.path_prefix = "tmp_session_files"
        else:
            self.path_prefix = self.config.get("path_prefix", "results")

    def store(self, results, type: STORETYPE):
        # We only care about zipping working directories during EVALS storage
        if type != STORETYPE.EVALS:
            return

        if not self.bucket_name:
            logging.warning("GCS bucket name not provided in config.")
            return

        if not isinstance(results, pd.DataFrame):
            logging.warning("Results is not a DataFrame, skipping GCS upload.")
            return

        if "working_dir" not in results.columns:
            logging.warning("No working_dir in results dataframe.")
            return

        bucket = self.client.bucket(self.bucket_name)
        unique_dirs = results["working_dir"].dropna().unique()

        if len(unique_dirs) == 1:
            working_dir = unique_dirs[0]
            if len(results) > 1:
                logging.info(f"Detected shared working directory: {working_dir}")
                self._zip_and_upload(working_dir, "shared_working_dir", bucket)
            else:
                eval_id = results["eval_id"].iloc[0]
                self._zip_and_upload(working_dir, eval_id, bucket)
        else:
            for working_dir in unique_dirs:
                rows = results[results["working_dir"] == working_dir]
                if len(rows) > 1:
                    eval_id = f"shared_{rows['eval_id'].iloc[0]}"
                else:
                    eval_id = rows["eval_id"].iloc[0]
                
                self._zip_and_upload(working_dir, eval_id, bucket)

    def _zip_and_upload(self, src_dir, eval_id, bucket):
        if not os.path.exists(src_dir):
            logging.warning(f"Source directory {src_dir} does not exist.")
            return

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            zip_path = tmp_file.name

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(src_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, src_dir)
                        zipf.write(file_path, arcname)

            blob_name = f"{self.path_prefix}/{self.job_id}/{eval_id}.zip"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(zip_path)
            logging.info(f"Uploaded {src_dir} to gs://{self.bucket_name}/{blob_name}")

        except Exception as e:
            logging.error(f"Failed to upload {src_dir} to GCS: {e}")
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)
