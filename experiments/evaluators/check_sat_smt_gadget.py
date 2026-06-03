"""Check the tiny SAT/SMT pilot construction."""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml  # type: ignore[import-untyped]

CHECKER_MARKER = "CHECKER_DATA:\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_sat_smt_gadget.py <artifact-yaml>", file=sys.stderr)
        return 2

    artifact_path = Path(argv[1])
    if not artifact_path.exists():
        print(f"artifact not found: {artifact_path}", file=sys.stderr)
        return 2

    artifact = yaml.safe_load(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        print("artifact YAML root must be a mapping", file=sys.stderr)
        return 1

    errors = check_sat_smt_gadget_artifact(artifact, repo_root=Path.cwd())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    data = _load_checker_data(str(artifact["statement"]))
    cnf = _parse_dimacs(_resolve_path(data["cnf_path"], repo_root=Path.cwd()))
    print(
        "tiny SAT gadget verified: "
        f"{cnf.variable_count} variables, {len(cnf.clauses)} clauses"
    )
    return 0


def check_sat_smt_gadget_artifact(
    artifact: dict[str, Any],
    *,
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    if artifact.get("type") != "construction":
        errors.append("artifact type must be construction")
    if artifact.get("status") not in {"draft", "locally_tested"}:
        errors.append("artifact status must remain draft or locally_tested")
    if "satisfiability" not in artifact.get("domain", []):
        errors.append("artifact domain must include satisfiability")

    statement = artifact.get("statement")
    if not isinstance(statement, str):
        errors.append("artifact statement must be a string")
        return errors

    try:
        data = _load_checker_data(statement)
        cnf = _parse_dimacs(_resolve_path(data["cnf_path"], repo_root=repo_root))
        assignment_data = _load_assignment(
            _resolve_path(data["assignment_path"], repo_root=repo_root)
        )
    except (KeyError, ValueError, OSError) as exc:
        errors.append(str(exc))
        return errors

    errors.extend(_validate_expected(data, assignment_data, cnf))
    if errors:
        return errors

    assignment = assignment_data["assignment"]
    errors.extend(_validate_assignment_coverage(cnf, assignment))
    errors.extend(_validate_clause_satisfaction(cnf, assignment))
    return errors


class CnfFormula:
    """A tiny parsed DIMACS CNF formula."""

    def __init__(self, variable_count: int, clauses: tuple[tuple[int, ...], ...]):
        self.variable_count = variable_count
        self.clauses = clauses


def _load_checker_data(statement: str) -> dict[str, Any]:
    if CHECKER_MARKER not in statement:
        raise ValueError("statement is missing CHECKER_DATA block")
    raw_data = statement.split(CHECKER_MARKER, 1)[1]
    data = yaml.safe_load(dedent(raw_data))
    if not isinstance(data, dict):
        raise ValueError("CHECKER_DATA must parse as a mapping")
    return data


def _resolve_path(value: Any, *, repo_root: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"expected non-empty path string, got {value!r}")
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def _parse_dimacs(path: Path) -> CnfFormula:
    if not path.exists():
        raise ValueError(f"CNF file not found: {path}")

    variable_count: int | None = None
    expected_clause_count: int | None = None
    clauses: list[tuple[int, ...]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p "):
            parts = line.split()
            if len(parts) != 4 or parts[1] != "cnf":
                raise ValueError(f"invalid DIMACS header on line {line_number}")
            variable_count = _parse_positive_int(parts[2], "variable count")
            expected_clause_count = _parse_positive_int(parts[3], "clause count")
            continue
        literals = [_parse_int(part, line_number) for part in line.split()]
        if not literals or literals[-1] != 0:
            raise ValueError(f"clause on line {line_number} must end with 0")
        clause = tuple(literal for literal in literals[:-1] if literal != 0)
        if not clause:
            raise ValueError(f"empty clause on line {line_number}")
        clauses.append(clause)

    if variable_count is None or expected_clause_count is None:
        raise ValueError("DIMACS file is missing p cnf header")
    if expected_clause_count != len(clauses):
        raise ValueError(
            "DIMACS clause count mismatch: "
            f"header {expected_clause_count}, parsed {len(clauses)}"
        )
    _validate_literal_range(variable_count, clauses)
    return CnfFormula(variable_count=variable_count, clauses=tuple(clauses))


def _load_assignment(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"assignment file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("assignment YAML root must be a mapping")
    assignment = raw.get("assignment")
    expected = raw.get("expected")
    if not isinstance(assignment, dict):
        raise ValueError("assignment must be a mapping")
    if not isinstance(expected, dict):
        raise ValueError("expected must be a mapping")
    normalized_assignment: dict[int, bool] = {}
    for key, value in assignment.items():
        variable = _parse_positive_int(str(key), "assignment variable")
        if not isinstance(value, bool):
            raise ValueError(f"assignment for variable {variable} must be boolean")
        normalized_assignment[variable] = value
    return {"assignment": normalized_assignment, "expected": expected}


def _validate_expected(
    checker_data: dict[str, Any],
    assignment_data: dict[str, Any],
    cnf: CnfFormula,
) -> list[str]:
    errors: list[str] = []
    statement_expected = checker_data.get("expected")
    assignment_expected = assignment_data["expected"]
    if not isinstance(statement_expected, dict):
        return ["CHECKER_DATA expected must be a mapping"]

    for source_name, expected in (
        ("CHECKER_DATA", statement_expected),
        ("assignment", assignment_expected),
    ):
        if expected.get("variables") != cnf.variable_count:
            errors.append(
                f"{source_name} variable count mismatch: "
                f"expected {expected.get('variables')!r}, parsed {cnf.variable_count}"
            )
        if expected.get("clauses") != len(cnf.clauses):
            errors.append(
                f"{source_name} clause count mismatch: "
                f"expected {expected.get('clauses')!r}, parsed {len(cnf.clauses)}"
            )
        if expected.get("satisfiable") is not True:
            errors.append(f"{source_name} must record satisfiable: true")
    return errors


def _validate_assignment_coverage(
    cnf: CnfFormula,
    assignment: dict[int, bool],
) -> list[str]:
    missing = [
        variable
        for variable in range(1, cnf.variable_count + 1)
        if variable not in assignment
    ]
    if not missing:
        return []
    return [f"assignment is missing variable(s): {missing}"]


def _validate_clause_satisfaction(
    cnf: CnfFormula,
    assignment: dict[int, bool],
) -> list[str]:
    errors: list[str] = []
    satisfied_count = 0
    for index, clause in enumerate(cnf.clauses, start=1):
        if _clause_satisfied(clause, assignment):
            satisfied_count += 1
            continue
        errors.append(f"clause {index} is not satisfied: {clause}")
    if satisfied_count != len(cnf.clauses):
        errors.append(
            "satisfied clause count mismatch: "
            f"expected {len(cnf.clauses)}, computed {satisfied_count}"
        )
    return errors


def _clause_satisfied(clause: tuple[int, ...], assignment: dict[int, bool]) -> bool:
    return any(_literal_satisfied(literal, assignment) for literal in clause)


def _literal_satisfied(literal: int, assignment: dict[int, bool]) -> bool:
    value = assignment[abs(literal)]
    return value if literal > 0 else not value


def _parse_positive_int(value: str, label: str) -> int:
    parsed = _parse_raw_int(value, label)
    if parsed <= 0:
        raise ValueError(f"{label} must be positive: {value}")
    return parsed


def _parse_int(value: str, line_number: int) -> int:
    return _parse_raw_int(value, f"integer literal on line {line_number}")


def _parse_raw_int(value: str, label: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value}") from exc


def _validate_literal_range(
    variable_count: int,
    clauses: list[tuple[int, ...]],
) -> None:
    for clause in clauses:
        for literal in clause:
            if abs(literal) > variable_count:
                raise ValueError(
                    f"literal {literal} exceeds variable count {variable_count}"
                )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
