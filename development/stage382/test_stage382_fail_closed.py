#!/usr/bin/env python3
"""
Fail-Closed tests for Stage382.

These tests use temporary copies of the repository inputs.
They do not modify the real Stage377 through Stage381 records.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

VERIFIER_RELATIVE_PATH = Path(
    "development/stage382/"
    "verify_stage382_upstream_finalization.py"
)

RESULT_RELATIVE_PATH = Path(
    "development/stage382/"
    "stage382_upstream_finalization_result.json"
)

POLICY_PROFILE_RELATIVE_PATH = Path(
    "development/stage382/policy-profiles/"
    "qsp-dual-timestamp-final-acceptance-v1.json"
)

POLICY_SHA256_RELATIVE_PATH = Path(
    "development/stage382/policy-profiles/"
    "qsp-dual-timestamp-final-acceptance-v1.sha256"
)

STAGE377_RELATIVE_PATH = Path(
    "docs/timestamp-finalization/"
    "stage377_dual_timestamp_finalization_result.json"
)

STAGE378_RELATIVE_PATH = Path(
    "docs/qkd/"
    "stage378_qkd_safety_metadata_binding_result.json"
)

STAGE380_RELATIVE_PATH = Path(
    "development/stage380/"
    "stage380_independent_verification_result.json"
)

STAGE381_RELATIVE_PATH = Path(
    "docs/verification/stage381/"
    "stage381_cross_platform_verification_package_result.json"
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise TypeError(f"JSON root must be object: {path}")

    return data


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


class Stage382FailClosedTests(unittest.TestCase):
    temporary_directory: tempfile.TemporaryDirectory[str]
    worktree: Path

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.worktree = Path(self.temporary_directory.name) / "repo"

        shutil.copytree(
            REPOSITORY_ROOT,
            self.worktree,
            ignore=shutil.ignore_patterns(
                ".git",
                "__pycache__",
                "*.pyc",
            ),
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_verifier(self) -> tuple[int, dict[str, Any]]:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.worktree / VERIFIER_RELATIVE_PATH),
            ],
            cwd=self.worktree,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        result_path = self.worktree / RESULT_RELATIVE_PATH

        self.assertTrue(
            result_path.is_file(),
            msg=(
                "Stage382 result was not generated.\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            ),
        )

        return completed.returncode, load_json(result_path)

    def rewrite_policy_sha256_record(self) -> None:
        profile_path = (
            self.worktree / POLICY_PROFILE_RELATIVE_PATH
        )

        record_path = (
            self.worktree / POLICY_SHA256_RELATIVE_PATH
        )

        digest = hashlib.sha256(
            profile_path.read_bytes()
        ).hexdigest()

        record_path.write_text(
            (
                f"{digest}  "
                f"{POLICY_PROFILE_RELATIVE_PATH.as_posix()}\n"
            ),
            encoding="utf-8",
            newline="\n",
        )

    def test_current_pending_state_is_verified_pending(self) -> None:
        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            result.get("decision"),
            "policy_bound_final_acceptance_pending",
        )
        self.assertEqual(
            result.get("verification_status"),
            "verified_pending_upstream",
        )
        self.assertFalse(
            result.get("formal_acceptance")
        )
        self.assertFalse(
            result.get("pipeline_completed")
        )
        self.assertFalse(
            result.get(
                "upstream_state",
                {},
            ).get("stage377_complete")
        )
        self.assertEqual(
            result.get("critical_failure_count"),
            0,
        )

    def test_incomplete_stage377_is_not_upgraded(self) -> None:
        stage377_path = (
            self.worktree / STAGE377_RELATIVE_PATH
        )

        stage377 = load_json(stage377_path)

        stage377["verified_proof_count"] = 1
        stage377["effective_final_acceptance"] = False
        stage377["decision"] = (
            "rfc3161_verified_opentimestamps_pending"
        )

        write_json(stage377_path, stage377)

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            result.get("decision"),
            "policy_bound_final_acceptance_pending",
        )
        self.assertFalse(
            result.get(
                "policy_activation_state",
                {},
            ).get("policy_activated")
        )
        self.assertFalse(
            result.get("formal_acceptance")
        )

    def test_policy_sha256_tampering_fails_closed(self) -> None:
        record_path = (
            self.worktree / POLICY_SHA256_RELATIVE_PATH
        )

        record_path.write_text(
            (
                "0" * 64
                + "  "
                + POLICY_PROFILE_RELATIVE_PATH.as_posix()
                + "\n"
            ),
            encoding="utf-8",
            newline="\n",
        )

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            result.get("decision"),
            "fail_closed",
        )
        self.assertIn(
            "policy_sha256_valid",
            result.get("critical_failures", []),
        )

    def test_missing_required_file_fails_closed(self) -> None:
        stage377_path = (
            self.worktree / STAGE377_RELATIVE_PATH
        )

        stage377_path.unlink()

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            result.get("decision"),
            "fail_closed",
        )
        self.assertEqual(
            result.get("verification_status"),
            "error",
        )
        self.assertIn(
            "stage382_execution_error",
            result.get("critical_failures", []),
        )

    def test_stage380_integrity_failure_fails_closed(self) -> None:
        stage380_path = (
            self.worktree / STAGE380_RELATIVE_PATH
        )

        stage380 = load_json(stage380_path)
        stage380["package_integrity_verified"] = False
        stage380["critical_failure_count"] = 1

        write_json(stage380_path, stage380)

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            result.get("decision"),
            "fail_closed",
        )
        self.assertIn(
            "stage380_package_integrity_verified",
            result.get("critical_failures", []),
        )
        self.assertIn(
            "stage380_critical_failure_count_zero",
            result.get("critical_failures", []),
        )

    def test_stage381_reproducibility_failure_fails_closed(
        self,
    ) -> None:
        stage381_path = (
            self.worktree / STAGE381_RELATIVE_PATH
        )

        stage381 = load_json(stage381_path)

        stage381[
            "cross_platform_reverification_verified"
        ] = False

        stage381[
            "same_canonical_result_sha256_verified"
        ] = False

        stage381["critical_failure_count"] = 2

        write_json(stage381_path, stage381)

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            result.get("decision"),
            "fail_closed",
        )
        self.assertIn(
            "stage381_cross_platform_reverification_verified",
            result.get("critical_failures", []),
        )
        self.assertIn(
            "stage381_same_canonical_result_sha256_verified",
            result.get("critical_failures", []),
        )
        self.assertIn(
            "stage381_critical_failure_count_zero",
            result.get("critical_failures", []),
        )

    def test_completed_stage377_requires_stage378_reverification(
        self,
    ) -> None:
        stage377_path = (
            self.worktree / STAGE377_RELATIVE_PATH
        )

        stage377 = load_json(stage377_path)

        stage377["verified_proof_count"] = 2
        stage377["effective_final_acceptance"] = True
        stage377["decision"] = (
            "dual_timestamp_final_acceptance_verified"
        )

        write_json(stage377_path, stage377)

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            result.get("decision"),
            "policy_bound_stage378_reverification_required",
        )
        self.assertEqual(
            result.get("verification_status"),
            "stage377_complete_stage378_pending",
        )
        self.assertTrue(
            result.get(
                "policy_activation_state",
                {},
            ).get("policy_activated")
        )
        self.assertTrue(
            result.get(
                "policy_activation_state",
                {},
            ).get(
                "stage378_reverification_required"
            )
        )
        self.assertFalse(
            result.get(
                "policy_activation_state",
                {},
            ).get(
                "downstream_reverification_required"
            )
        )
        self.assertFalse(
            result.get("formal_acceptance")
        )
        self.assertFalse(
            result.get("pipeline_completed")
        )

    def test_completed_stage377_and_stage378_require_downstream_reverification(
        self,
    ) -> None:
        stage377_path = (
            self.worktree / STAGE377_RELATIVE_PATH
        )

        stage378_path = (
            self.worktree / STAGE378_RELATIVE_PATH
        )

        stage377 = load_json(stage377_path)
        stage378 = load_json(stage378_path)

        stage377["verified_proof_count"] = 2
        stage377["effective_final_acceptance"] = True
        stage377["decision"] = (
            "dual_timestamp_final_acceptance_verified"
        )

        stage378["stage377_hash_valid"] = True
        stage378[
            "stage377_final_acceptance_verified"
        ] = True
        stage378["qkd_metadata_bound"] = True
        stage378[
            "raw_qkd_key_publication_detected"
        ] = False
        stage378[
            "private_material_content_detected"
        ] = False
        stage378["forbidden_public_files"] = []
        stage378["decision"] = (
            "qkd_safety_metadata_bound"
        )

        write_json(stage377_path, stage377)
        write_json(stage378_path, stage378)

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            result.get("decision"),
            (
                "policy_bound_upstream_finalization_ready_"
                "for_downstream_reverification"
            ),
        )
        self.assertEqual(
            result.get("verification_status"),
            (
                "stage377_and_stage378_complete_"
                "downstream_reverification_required"
            ),
        )
        self.assertTrue(
            result.get(
                "policy_activation_state",
                {},
            ).get("policy_activated")
        )
        self.assertTrue(
            result.get(
                "policy_activation_state",
                {},
            ).get("stage378_ready")
        )
        self.assertFalse(
            result.get(
                "policy_activation_state",
                {},
            ).get(
                "stage378_reverification_required"
            )
        )
        self.assertTrue(
            result.get(
                "policy_activation_state",
                {},
            ).get(
                "downstream_reverification_required"
            )
        )
        self.assertFalse(
            result.get(
                "policy_activation_state",
                {},
            ).get(
                "automatic_acceptance_upgrade_performed"
            )
        )
        self.assertFalse(
            result.get("formal_acceptance")
        )
        self.assertFalse(
            result.get("pipeline_completed")
        )

    def test_stage378_publication_boundary_failure_fails_closed(
        self,
    ) -> None:
        stage378_path = (
            self.worktree / STAGE378_RELATIVE_PATH
        )

        stage378 = load_json(stage378_path)

        stage378[
            "raw_qkd_key_publication_detected"
        ] = True
        stage378["forbidden_public_files"] = [
            "docs/qkd/example-secret-key.bin"
        ]

        write_json(stage378_path, stage378)

        exit_code, result = self.run_verifier()

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            result.get("decision"),
            "fail_closed",
        )
        self.assertIn(
            "stage378_raw_qkd_key_not_published",
            result.get("critical_failures", []),
        )
        self.assertIn(
            "stage378_forbidden_public_files_empty",
            result.get("critical_failures", []),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
