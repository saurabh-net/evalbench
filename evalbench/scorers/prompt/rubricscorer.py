RUBRIC_EVAL_PROMPT = """
You are an expert evaluator assessing whether an AI agent successfully completed its assigned task according to a specific rubric.

### Input Data
**Rubric Criteria:**
{rubric_items}

**Conversation History:**
{conversation_history}

### Task
Determine if the agent successfully fulfilled the requirements specified in the rubric.
You must check each criterion in the rubric.

### Output Format
Provide your response in the following format:
The first line must specify how many rubric criteria were satisfied, in the format: "Passed criteria: M/N".
Where M is the number of criteria satisfied, and N is the total number of criteria.

Followed by your reasoning, analyzing each point of the rubric:
Reasoning:
- Point 1: [PASS/FAIL] [Reasoning]
- Point 2: [PASS/FAIL] [Reasoning]
...
"""
