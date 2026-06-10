from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "cosheaf-operator"


def test_cosheaf_operator_skill_package_is_structurally_valid() -> None:
    skill = SKILL_DIR / "SKILL.md"
    openai_yaml = SKILL_DIR / "agents" / "openai.yaml"
    reference = SKILL_DIR / "references" / "cli-first-workflow.md"

    assert skill.is_file()
    assert openai_yaml.is_file()
    assert reference.is_file()

    skill_text = skill.read_text(encoding="utf-8")
    assert skill_text.startswith("---\n")
    frontmatter = yaml.safe_load(skill_text.split("---\n", 2)[1])
    assert frontmatter["name"] == "cosheaf-operator"
    assert "TCS-Cosheaf" in frontmatter["description"]

    metadata = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
    assert metadata["interface"]["display_name"] == "Cosheaf Operator"
    assert "$cosheaf-operator" in metadata["interface"]["default_prompt"]
    assert metadata["policy"]["allow_implicit_invocation"] is True


def test_cosheaf_operator_skill_preserves_governance_boundaries() -> None:
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    reference = (SKILL_DIR / "references" / "cli-first-workflow.md").read_text(
        encoding="utf-8"
    )
    combined = f"{text}\n{reference}"

    required_phrases = [
        "CLI-first workflow",
        "MCP is optional",
        "not required",
        "write directly to `kb/accepted/`",
        "mark AI output as `human_reviewed`",
        "treat skipped verifier or provider results as passes",
        "not accepted knowledge",
    ]

    for phrase in required_phrases:
        assert phrase in combined

    assert "WorkerBundle" in combined
    assert "review context only" in combined
