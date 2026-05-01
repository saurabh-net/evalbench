import os
import logging
import sys
from reporting.report import Reporter, STORETYPE
from google.cloud import storage
import pandas as pd

class GcsReporter(Reporter):
    def __init__(self, reporting_config, job_id, run_time):
        super().__init__(reporting_config, job_id, run_time)
        self.bucket_name = reporting_config.get("bucket")
        self.client = storage.Client()
        
        # Similar to csv.py, we can have a path prefix
        if sys.argv[0].endswith("eval_server.py"):
             self.path_prefix = "results"
        else:
             self.path_prefix = self.config.get("path_prefix", "results")

    def store(self, results, type: STORETYPE):
        if not self.bucket_name:
            logging.warning("GCS bucket name not provided in config.")
            return

        if not isinstance(results, pd.DataFrame):
            logging.warning("Results is not a DataFrame, skipping GCS upload.")
            return

        bucket = self.client.bucket(self.bucket_name)

        if type == STORETYPE.CONFIGS:
            blob_name = f"{self.path_prefix}/{self.job_id}/configs.csv"
        elif type == STORETYPE.EVALS:
            blob_name = f"{self.path_prefix}/{self.job_id}/evals.csv"
        elif type == STORETYPE.SCORES:
            blob_name = f"{self.path_prefix}/{self.job_id}/scores.csv"
        elif type == STORETYPE.SUMMARY:
            blob_name = f"{self.path_prefix}/{self.job_id}/summary.csv"
        else:
            logging.warning(f"Unknown STORETYPE: {type}")
            return

        try:
            csv_string = results.to_csv(index=False)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(csv_string, content_type='text/csv')
            logging.info(f"Uploaded {type} to gs://{self.bucket_name}/{blob_name}")
        except Exception as e:
            logging.error(f"Failed to upload {type} to GCS: {e}")
