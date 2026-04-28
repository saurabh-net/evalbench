import unittest
from unittest.mock import patch, MagicMock
from evalbench.reporting.gcs import GcsArtifactReporter
from evalbench.reporting.report import STORETYPE


class TestGcsArtifactReporter(unittest.TestCase):

    @patch('evalbench.reporting.gcs.storage.Client')
    @patch('evalbench.reporting.gcs.subprocess.run')
    def test_store_git_diff_and_metadata(self, mock_subproc_run, mock_storage_client):
        # 1. Set up Git mock responses
        mock_toplevel = MagicMock()
        mock_toplevel.returncode = 0
        mock_toplevel.stdout = "/fake/toplevel\n"

        mock_diff = MagicMock()
        mock_diff.stdout = "diff --git a/file1.py b/file1.py\n+added_line\n"

        mock_status = MagicMock()
        mock_status.stdout = " M file1.py\n"

        mock_commit = MagicMock()
        mock_commit.stdout = "abc123commit\n"

        mock_remote = MagicMock()
        mock_remote.stdout = "https://github.com/fake/repo.git\n"

        mock_subproc_run.side_effect = [
            mock_toplevel,
            mock_diff,
            mock_status,
            mock_commit,
            mock_remote,
        ]

        # 2. Set up GCS Client Mocking
        mock_bucket = MagicMock()
        mock_blob_diff = MagicMock()
        mock_blob_meta = MagicMock()
        
        # When bucket.blob() is called, return specific mock blobs
        mock_bucket.blob.side_effect = [mock_blob_diff, mock_blob_meta]

        mock_client = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client

        # Initialize reporter
        reporting_config = {
            "bucket": "test-artifacts-bucket",
            "output_directory": "results/artifacts"
        }
        reporter = GcsArtifactReporter(reporting_config, "job123", "10s")

        # Call store
        reporter.store(None, STORETYPE.CONFIGS)

        # Assert that code was captured and uploaded
        self.assertTrue(reporter.uploaded)
        mock_client.bucket.assert_called_with("test-artifacts-bucket")
        
        # Assert it called upload_from_string with diff and metadata
        mock_blob_diff.upload_from_string.assert_called_once_with("diff --git a/file1.py b/file1.py\n+added_line\n")
        mock_blob_meta.upload_from_string.assert_called_once()

    @patch('evalbench.reporting.gcs.storage.Client')
    @patch('evalbench.reporting.gcs.subprocess.run')
    def test_store_no_bucket_skip(self, mock_subproc_run, mock_storage_client):
        reporting_config = {}
        reporter = GcsArtifactReporter(reporting_config, "job123", "10s")
        reporter.store(None, STORETYPE.CONFIGS)
        self.assertTrue(reporter.uploaded)
        mock_storage_client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
