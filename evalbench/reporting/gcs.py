import os
import glob
import logging
import subprocess
import sys
from datetime import datetime
import json
from google.cloud import storage
from .report import Reporter, STORETYPE

class GcsArtifactReporter(Reporter):
    def __init__(self, reporting_config, job_id, run_time):
        super().__init__(reporting_config, job_id, run_time)
        self.bucket_name = self.config.get("bucket")
        self.base_path = self.config.get("output_directory", "artifacts").strip("/")
        self.include_files = self.config.get("include_files", [])
        self.uploaded = False

    def store(self, results, type: STORETYPE):
        if self.uploaded:
            return

        if not self.bucket_name:
            logging.warning("GCS Artifact Reporter: No bucket name configured.")
            self.uploaded = True
            return

        try:
            self._capture_and_upload_code_state()
        except Exception as e:
            logging.exception(f"GCS Artifact Reporter: Failed to capture/upload code state: {e}")
        finally:
            self.uploaded = True

    def _capture_and_upload_code_state(self):
        client = storage.Client()
        bucket = client.bucket(self.bucket_name)

        dest_prefix = f"{self.base_path}/{self.job_id}" if self.base_path else self.job_id

        # 1. Capture Git State
        git_diff, git_meta = self._capture_git_state()

        if git_diff:
            blob = bucket.blob(f"{dest_prefix}/code_diff.patch")
            blob.upload_from_string(git_diff)
            logging.info(f"Uploaded code diff to gs://{self.bucket_name}/{dest_prefix}/code_diff.patch")

        if git_meta:
            blob = bucket.blob(f"{dest_prefix}/git_metadata.json")
            blob.upload_from_string(git_meta, content_type="application/json")
            logging.info(f"Uploaded git metadata to gs://{self.bucket_name}/{dest_prefix}/git_metadata.json")

        # 2. Capture Config and Script files
        config_files = []
        for arg in sys.argv:
            if arg.endswith(".yaml") or arg.endswith(".json") or arg.endswith(".csv"):
                if os.path.exists(arg):
                    config_files.append(arg)

        if self.include_files:
            for pattern in self.include_files:
                for filename in glob.glob(pattern):
                    if os.path.isfile(filename):
                        config_files.append(filename)

        # deduplicate
        config_files = list(set(config_files))

        for cf in config_files:
            cf_basename = os.path.basename(cf)
            blob = bucket.blob(f"{dest_prefix}/configs/{cf_basename}")
            blob.upload_from_filename(cf)
            logging.info(f"Uploaded config file {cf} to gs://{self.bucket_name}/{dest_prefix}/configs/{cf_basename}")

    def _capture_git_state(self):
        git_diff = None
        git_meta = None
        try:
            res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            if res.returncode == 0:
                toplevel = res.stdout.strip()

                diff_res = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, cwd=toplevel)
                git_diff = diff_res.stdout

                untracked_res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=toplevel)
                git_status = untracked_res.stdout

                commit_res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=toplevel)
                commit_hash = commit_res.stdout.strip()

                remote_res = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, cwd=toplevel)
                remote_url = remote_res.stdout.strip()

                meta = {
                    "base_commit": commit_hash,
                    "remote_url": remote_url,
                    "git_status": git_status,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                git_meta = json.dumps(meta, indent=2)
        except Exception as e:
            logging.debug(f"Git state capture skipped/failed: {e}")

        return git_diff, git_meta

def upload_scenario_artifacts(reporting_config: dict, job_id: str, scenario_id: str, scenario_cwd: str):
    """Captures and uploads the scenario's git diff to GCS."""
    bucket_name = reporting_config.get("bucket")
    if not bucket_name:
        logging.warning("Scenario GCS Uploader: No bucket configured.")
        return

    base_path = reporting_config.get("output_directory", "artifacts").strip("/")
    dest_prefix = f"{base_path}/{job_id}/{scenario_id}" if base_path else f"{job_id}/{scenario_id}"

    try:
        logging.info(f"Scenario {scenario_id}: Files in scenario_cwd before add: {os.listdir(scenario_cwd)}")
        
        # Add untracked files to the index so they are included in the diff
        subprocess.run(["git", "add", "-A"], cwd=scenario_cwd, capture_output=True, check=False)
        
        # Capture the git diff of the scenario's ephemeral workspace
        res = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, cwd=scenario_cwd)
        git_diff = res.stdout

        logging.info(f"Scenario {scenario_id}: Captured git diff. Length: {len(git_diff if git_diff else '')} bytes. Stderr: {res.stderr}")
        if git_diff:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(f"{dest_prefix}/code_diff.patch")
            blob.upload_from_string(git_diff)
            logging.info(f"Uploaded scenario code diff to gs://{bucket_name}/{dest_prefix}/code_diff.patch")
    except Exception as e:
        logging.error(f"Scenario GCS Uploader: Failed to upload scenario artifacts: {e}")
