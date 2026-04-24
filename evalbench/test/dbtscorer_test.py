import unittest
from unittest.mock import patch, MagicMock
import os
from scorers.dbtscorer import DbtCompileScorer, DbtRunScorer


class TestDbtScorer(unittest.TestCase):

    @patch('scorers.dbtscorer.shutil.which')
    @patch('scorers.dbtscorer._find_project_dir')
    @patch('scorers.dbtscorer.subprocess.run')
    def test_dbt_compile_pass(self, mock_run, mock_find_dir, mock_which):
        mock_which.return_value = "/usr/bin/dbt"
        mock_find_dir.return_value = "/path/to/project"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        scorer = DbtCompileScorer({})
        score, reason = scorer.compare(
            nl_prompt="", golden_query="", query_type="",
            golden_execution_result="", golden_eval_result="", golden_error="",
            generated_query="", generated_execution_result="", generated_eval_result="", generated_error=""
        )

        self.assertEqual(score, 100.0)
        self.assertEqual(reason, "PASS")
        mock_run.assert_called_once()

    @patch('scorers.dbtscorer.shutil.which')
    @patch('scorers.dbtscorer._find_project_dir')
    @patch('scorers.dbtscorer.subprocess.run')
    def test_dbt_compile_fail(self, mock_run, mock_find_dir, mock_which):
        mock_which.return_value = "/usr/bin/dbt"
        mock_find_dir.return_value = "/path/to/project"
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Compile error"
        mock_run.return_value = mock_result

        scorer = DbtCompileScorer({})
        score, reason = scorer.compare(
            nl_prompt="", golden_query="", query_type="",
            golden_execution_result="", golden_eval_result="", golden_error="",
            generated_query="", generated_execution_result="", generated_eval_result="", generated_error=""
        )

        self.assertEqual(score, 0.0)
        self.assertIn("FAIL: Compile error", reason)

    @patch('scorers.dbtscorer.shutil.which')
    def test_dbt_not_setup(self, mock_which):
        mock_which.return_value = None

        scorer = DbtCompileScorer({})
        score, reason = scorer.compare(
            nl_prompt="", golden_query="", query_type="",
            golden_execution_result="", golden_eval_result="", golden_error="",
            generated_query="", generated_execution_result="", generated_eval_result="", generated_error=""
        )

        self.assertEqual(score, 0.0)
        self.assertEqual(reason, "dbt not setup, unable to run the scorer")

    @patch('scorers.dbtscorer.shutil.which')
    @patch('scorers.dbtscorer.os.walk')
    def test_project_not_found(self, mock_walk, mock_which):
        mock_which.return_value = "/usr/bin/dbt"
        mock_walk.return_value = [(".", [], [])] # Empty dir

        scorer = DbtCompileScorer({})
        score, reason = scorer.compare(
            nl_prompt="", golden_query="", query_type="",
            golden_execution_result="", golden_eval_result="", golden_error="",
            generated_query="", generated_execution_result="", generated_eval_result="", generated_error=""
        )

        self.assertEqual(score, 0.0)
        self.assertIn("FAIL: Could not find dbt_project.yml", reason)

if __name__ == '__main__':
    unittest.main()
