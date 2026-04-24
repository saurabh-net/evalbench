from typing import Tuple, Any
import logging
from scorers import comparator
import subprocess
import os
import shutil

def _find_project_dir(start_dir: str, filename: str) -> str:
    """Searches for a file starting from start_dir and returns its directory."""
    for root, dirs, files in os.walk(start_dir):
        if filename in files:
            return root
    raise FileNotFoundError(f"Could not find {filename} in {start_dir}")

def _has_profiles_yml(project_dir: str) -> bool:
    """Checks if profiles.yml exists in the project directory."""
    return os.path.exists(os.path.join(project_dir, "profiles.yml"))

class DbtBaseScorer(comparator.Comparator):
    """Base class for dbt scorers."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "dbt_base"

    def _check_dbt(self) -> bool:
        return shutil.which("dbt") is not None

    def _run_dbt_command(self, command_parts: list[str], project_dir: str) -> Tuple[float, str]:
        if not self._check_dbt():
            return 0.0, "dbt not setup, unable to run the scorer"

        try:
            result = subprocess.run(
                command_parts,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return 100.0, "PASS"
            else:
                return 0.0, f"FAIL: {result.stderr or result.stdout}"
        except Exception as e:
            return 0.0, f"Exception running dbt: {e}"

class DbtCompileScorer(DbtBaseScorer):
    """Validates that the dbt project compiles successfully."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "dbt_compile"

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
        if not self._check_dbt():
            return 0.0, "dbt not setup, unable to run the scorer"
        try:
            project_dir = _find_project_dir(".", "dbt_project.yml")
            command_parts = ["dbt", "compile", "--project-dir", project_dir]
            if _has_profiles_yml(project_dir):
                command_parts.extend(["--profiles-dir", project_dir])
            return self._run_dbt_command(command_parts, project_dir)
        except FileNotFoundError as e:
            return 0.0, f"FAIL: {e}"
        except Exception as e:
            return 0.0, f"FAIL: Exception: {e}"

class DbtRunScorer(DbtBaseScorer):
    """Validates that the dbt project runs successfully."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "dbt_run"

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
        if not self._check_dbt():
            return 0.0, "dbt not setup, unable to run the scorer"
        try:
            project_dir = _find_project_dir(".", "dbt_project.yml")
            command_parts = ["dbt", "run", "--project-dir", project_dir]
            if _has_profiles_yml(project_dir):
                command_parts.extend(["--profiles-dir", project_dir])
            return self._run_dbt_command(command_parts, project_dir)
        except FileNotFoundError as e:
            return 0.0, f"FAIL: {e}"
        except Exception as e:
            return 0.0, f"FAIL: Exception: {e}"
