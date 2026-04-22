import unittest
from unittest.mock import patch, MagicMock
from scorers.rubricscorer import RubricScorer


class TestRubricScorer(unittest.TestCase):

    @patch('scorers.rubricscorer.get_generator')
    def test_compare_rubric_pass(self, mock_get_generator):
        mock_model = MagicMock()
        mock_model.generate.return_value = "Passed criteria: 2/2\nAll criteria were satisfied."
        mock_get_generator.return_value = mock_model

        config = {"model_config": "fake_config"}
        scorer = RubricScorer(config, global_models={})

        score, reason = scorer.compare(
            nl_prompt="",
            golden_query="",
            query_type="",
            golden_execution_result="",
            golden_eval_result="",
            golden_error="",
            generated_query="",
            generated_execution_result="",
            generated_eval_result='{"conversation_history": "[]", "scenario": {"rubric": ["Criterion 1", "Criterion 2"]}}',
            generated_error=""
        )

        self.assertEqual(score, 100.0)
        self.assertIn("Passed criteria: 2/2", reason)
        mock_model.generate.assert_called_once()

    @patch('scorers.rubricscorer.get_generator')
    def test_compare_rubric_partial_fail(self, mock_get_generator):
        mock_model = MagicMock()
        mock_model.generate.return_value = "Passed criteria: 1/2\nCriterion 1 was not satisfied."
        mock_get_generator.return_value = mock_model

        config = {"model_config": "fake_config"}
        scorer = RubricScorer(config, global_models={})

        score, reason = scorer.compare(
            nl_prompt="",
            golden_query="",
            query_type="",
            golden_execution_result="",
            golden_eval_result="",
            golden_error="",
            generated_query="",
            generated_execution_result="",
            generated_eval_result='{"conversation_history": "[]", "scenario": {"rubric": ["Criterion 1", "Criterion 2"]}}',
            generated_error=""
        )

        self.assertEqual(score, 50.0)
        self.assertIn("Passed criteria: 1/2", reason)
        mock_model.generate.assert_called_once()


    @patch('scorers.rubricscorer.get_generator')
    def test_compare_missing_rubric_defaults_pass(self, mock_get_generator):
        mock_model = MagicMock()
        mock_get_generator.return_value = mock_model

        config = {"model_config": "fake_config"}
        scorer = RubricScorer(config, global_models={})

        score, reason = scorer.compare(
            nl_prompt="",
            golden_query="",
            query_type="",
            golden_execution_result="",
            golden_eval_result="",
            golden_error="",
            generated_query="",
            generated_execution_result="",
            generated_eval_result='{"conversation_history": "[]", "scenario": {}}',
            generated_error=""
        )

        self.assertEqual(score, 100.0)
        self.assertIn("No rubric defined", reason)
        mock_model.generate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
