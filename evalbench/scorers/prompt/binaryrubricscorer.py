BINARY_RUBRIC_EVAL_PROMPT = """
Analyze the conversation log and determine if the agent satisfied the
following criterion.

Criterion to evaluate:
{rubric_items}

Conversation Log:
{conversation_history}

Format your response as follows:
First line: "PASS" if the criterion was satisfied, or "FAIL" otherwise.
Subsequent lines: A brief explanation of your decision.
"""
