"""Exercise the CLI and native validation dependency without an Ollama server."""

import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel

from mediallm.safety.data_protection import SecretStr
from mediallm.utils.data_models import Action
from mediallm.utils.data_models import CommandEntry
from mediallm.utils.data_models import CommandPlan
from mediallm.utils.data_models import MediaIntent


def test_cli_help_starts_in_a_fresh_process(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c", "from mediallm.main import main; main()", "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "--model" in result.stdout


def test_media_intent_json_validation_and_schema():
    intent = MediaIntent.model_validate_json('{"action": "convert", "inputs": "input.mp4", "filters": "scale=640:360"}')

    assert intent.action == Action.convert
    assert intent.inputs == [Path("input.mp4")]
    assert intent.filters == ["scale=640:360"]
    assert intent.model_dump(mode="json")["inputs"] == ["input.mp4"]
    assert "inputs" in MediaIntent.model_json_schema()["properties"]


def test_command_plan_json_round_trip():
    plan = CommandPlan(
        summary="Extract audio",
        entries=[CommandEntry(input=Path("input.mp4"), output=Path("output.mp3"), args=["-vn"])],
    )

    assert CommandPlan.model_validate_json(plan.model_dump_json()) == plan
    assert "entries" in CommandPlan.model_json_schema()["properties"]


def test_custom_secret_core_schema_still_validates():
    class Credentials(BaseModel):
        token: SecretStr

    credentials = Credentials.model_validate_json('{"token": "example-private-value"}')

    assert credentials.token.get_secret_value() == "example-private-value"
    assert "example-private-value" not in repr(credentials)
    assert "token" in Credentials.model_json_schema()["properties"]
