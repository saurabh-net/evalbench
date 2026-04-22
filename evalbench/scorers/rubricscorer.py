from typing import Tuple, Any
import logging
from scorers import comparator
from generators.models import get_generator
from scorers.prompt.rubricscorer import RUBRIC_EVAL_PROMPT
import json


class RubricScorer(comparator.Comparator):
    """
    Evaluates whether the agent satisfied specific rubric criteria.
    """

    def __init__(self, config: dict, global_models):
        self.name = "rubric_scorer"
        self.model_config = config.get("model_config") or ""
        if not self.model_config:
            raise ValueError("model_config is required for RubricScorer")
        self.model = get_generator(global_models, self.model_config)

    def compare(
        self,
        nl_prompt: Any,
        golden_query: Any,
        query_type: Any,
        golden_execution_result: Any,
        golden_eval_result: Any,
        golden_error: Any,
        generated_query: Any,
        generated_execution_result: Any,
        generated_eval_result: Any,
        generated_error: Any,
    ) -> Tuple[float, str]:

        if not generated_eval_result:
            return 0.0, "No eval result context passed."

        try:
            context = (
                json.loads(generated_eval_result)
                if isinstance(generated_eval_result, str)
                else generated_eval_result
            )
        except json.JSONDecodeError:
            return 0.0, "Invalid JSON in eval result context."

        conversation_history = context.get("conversation_history", "[]")
        scenario = context.get("scenario", {})
        rubric = scenario.get("rubric", [])

        if not rubric:
            return 100.0, "No rubric defined for this scenario. Defaulting to PASS."

        rubric_str = "\n".join([f"- {criterion}" for criterion in rubric])

        prompt = RUBRIC_EVAL_PROMPT.format(
            rubric_items=rubric_str,
            conversation_history=conversation_history
        )

        try:
            response = self.model.generate(prompt)
            response_text = getattr(
                response, 'stdout', response) if response else ""
            if isinstance(response_text, str):
                first_line = response_text.strip().split('\n')[0].upper()
                score = 100.0 if "PASS" in first_line else 0.0
                return score, response_text
            return 0.0, "Failed to parse LLM evaluation response."
        except Exception as e:
            logging.error(f'RubricScorer generation failed: {e}')
            return 0.0, f"Error calling model: {e}"
