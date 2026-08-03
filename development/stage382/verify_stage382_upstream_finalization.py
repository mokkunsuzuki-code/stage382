#!/usr/bin/env python3
"""
Stage382 Upstream Finalization Recovery & Policy Activation Gate.

This verifier:
- preserves Stage377 through Stage381
- validates the Stage382 policy profile and SHA-256 record
- observes Stage377 completion state
- observes Stage379, Stage380, and Stage381 downstream state
- remains Fail-Closed while Stage377 is incomplete
- does not fabricate or automatically upgrade formal acceptance
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


STAGE = 382

DEVELOPMENT_POLICY_PATH = Path(
    ".stage382-development-policy.json"
)

POLICY_PROFILE_PATH = Path(
    "development/stage382/policy-profiles/"
    "qsp-dual-timestamp-final-acceptance-v1.json"
)

POLICY_SHA256_PATH = Path(
    "development/stage382/policy-profiles/"
    "qsp-dual-timestamp-final-acceptance-v1.sha256"
)

STAGE377_RESULT_PATH = Path(
    "docs/timestamp-finalization/"
    "stage377_dual_timestamp_finalization_result.json"
)

STAGE378_RESULT_PATH = Path(
    "docs/qkd/"
    "stage378_qkd_safety_metadata_binding_result.json"
)

STAGE379_RESULT_PATH = Path(
    "development/stage379/"
    "stage379_scoped_total_verification_result.json"
)

STAGE380_RESULT_PATH = Path(
    "development/stage380/"
    "stage380_independent_verification_result.json"
)

STAGE381_RESULT_PATH = Path(
    "docs/verification/stage381/"
    "stage381_cross_platform_verification_package_result.json"
)

OUTPUT_PATH = Path(
    "development/stage382/"
    "stage382_upstream_finalization_result.json"
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise TypeError(f"JSON root must be an object: {path}")

    return data


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    expected: Any,
    actual: Any,
    critical: bool = True,
) -> None:
    checks.append(
        {
            "name": name,
            "critical": critical,
            "passed": bool(passed),
            "expected": expected,
            "actual": actual,
        }
    )


def parse_sha256_record(path: Path) -> tuple[str, str]:
    parts = path.read_text(
        encoding="utf-8"
    ).strip().split(maxsplit=1)

    if len(parts) != 2:
        raise ValueError(
            f"invalid SHA-256 record format: {path}"
        )

    return parts[0], parts[1]


def main() -> int:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        required_files = (
            DEVELOPMENT_POLICY_PATH,
            POLICY_PROFILE_PATH,
            POLICY_SHA256_PATH,
            STAGE377_RESULT_PATH,
            STAGE378_RESULT_PATH,
            STAGE379_RESULT_PATH,
            STAGE380_RESULT_PATH,
            STAGE381_RESULT_PATH,
        )

        for required_file in required_files:
            add_check(
                checks,
                name=(
                    "required_file_present:"
                    + required_file.as_posix()
                ),
                passed=required_file.is_file(),
                expected=True,
                actual=required_file.is_file(),
            )

        missing_files = [
            path
            for path in required_files
            if not path.is_file()
        ]

        if missing_files:
            raise FileNotFoundError(
                "missing required file(s): "
                + ", ".join(
                    path.as_posix()
                    for path in missing_files
                )
            )

        development_policy = load_json(
            DEVELOPMENT_POLICY_PATH
        )
        policy_profile = load_json(
            POLICY_PROFILE_PATH
        )
        stage377 = load_json(
            STAGE377_RESULT_PATH
        )
        stage378 = load_json(
            STAGE378_RESULT_PATH
        )
        stage379 = load_json(
            STAGE379_RESULT_PATH
        )
        stage380 = load_json(
            STAGE380_RESULT_PATH
        )
        stage381 = load_json(
            STAGE381_RESULT_PATH
        )

        recorded_policy_hash, recorded_policy_path = (
            parse_sha256_record(POLICY_SHA256_PATH)
        )

        actual_policy_hash = sha256_file(
            POLICY_PROFILE_PATH
        )

        add_check(
            checks,
            name="policy_sha256_valid",
            passed=recorded_policy_hash == actual_policy_hash,
            expected=actual_policy_hash,
            actual=recorded_policy_hash,
        )

        add_check(
            checks,
            name="policy_sha256_record_path_valid",
            passed=(
                recorded_policy_path
                == POLICY_PROFILE_PATH.as_posix()
            ),
            expected=POLICY_PROFILE_PATH.as_posix(),
            actual=recorded_policy_path,
        )

        add_check(
            checks,
            name="policy_profile_name_valid",
            passed=(
                policy_profile.get("profile_name")
                == "qsp-dual-timestamp-final-acceptance-v1"
            ),
            expected="qsp-dual-timestamp-final-acceptance-v1",
            actual=policy_profile.get("profile_name"),
        )

        add_check(
            checks,
            name="policy_required_verified_proof_count",
            passed=(
                policy_profile.get(
                    "timestamp_requirements",
                    {},
                ).get(
                    "required_verified_proof_count"
                )
                == 2
            ),
            expected=2,
            actual=policy_profile.get(
                "timestamp_requirements",
                {},
            ).get(
                "required_verified_proof_count"
            ),
        )

        add_check(
            checks,
            name="policy_new_ots_proof_generation_forbidden",
            passed=(
                policy_profile.get(
                    "opentimestamps_requirements",
                    {},
                ).get(
                    "new_proof_generation_allowed"
                )
                is False
            ),
            expected=False,
            actual=policy_profile.get(
                "opentimestamps_requirements",
                {},
            ).get(
                "new_proof_generation_allowed"
            ),
        )

        stage377_verified_proof_count = (
            stage377.get("verified_proof_count")
        )

        stage377_effective_final_acceptance = (
            stage377.get(
                "effective_final_acceptance"
            )
        )

        stage377_decision = stage377.get("decision")

        stage377_complete = (
            stage377_verified_proof_count == 2
            and stage377_effective_final_acceptance is True
        )

        add_check(
            checks,
            name="stage377_verified_proof_count_complete",
            passed=stage377_verified_proof_count == 2,
            expected=2,
            actual=stage377_verified_proof_count,
            critical=False,
        )

        add_check(
            checks,
            name="stage377_effective_final_acceptance_complete",
            passed=(
                stage377_effective_final_acceptance is True
            ),
            expected=True,
            actual=stage377_effective_final_acceptance,
            critical=False,
        )


        stage378_ready = (
            stage378.get("stage377_hash_valid") is True
            and stage378.get(
                "stage377_final_acceptance_verified"
            ) is True
            and stage378.get("qkd_metadata_bound") is True
            and stage378.get(
                "raw_qkd_key_publication_detected"
            ) is False
            and stage378.get(
                "private_material_content_detected"
            ) is False
            and len(
                stage378.get(
                    "forbidden_public_files",
                    [],
                )
            ) == 0
        )

        add_check(
            checks,
            name="stage378_stage377_hash_valid",
            passed=(
                stage378.get("stage377_hash_valid")
                is True
            ),
            expected=True,
            actual=stage378.get(
                "stage377_hash_valid"
            ),
            critical=False,
        )

        add_check(
            checks,
            name="stage378_stage377_final_acceptance_verified",
            passed=(
                stage378.get(
                    "stage377_final_acceptance_verified"
                )
                is True
            ),
            expected=True,
            actual=stage378.get(
                "stage377_final_acceptance_verified"
            ),
            critical=False,
        )

        add_check(
            checks,
            name="stage378_qkd_metadata_bound",
            passed=(
                stage378.get("qkd_metadata_bound")
                is True
            ),
            expected=True,
            actual=stage378.get(
                "qkd_metadata_bound"
            ),
            critical=False,
        )

        add_check(
            checks,
            name="stage378_raw_qkd_key_not_published",
            passed=(
                stage378.get(
                    "raw_qkd_key_publication_detected"
                )
                is False
            ),
            expected=False,
            actual=stage378.get(
                "raw_qkd_key_publication_detected"
            ),
        )

        add_check(
            checks,
            name="stage378_private_material_not_detected",
            passed=(
                stage378.get(
                    "private_material_content_detected"
                )
                is False
            ),
            expected=False,
            actual=stage378.get(
                "private_material_content_detected"
            ),
        )

        add_check(
            checks,
            name="stage378_forbidden_public_files_empty",
            passed=(
                len(
                    stage378.get(
                        "forbidden_public_files",
                        [],
                    )
                )
                == 0
            ),
            expected=0,
            actual=len(
                stage378.get(
                    "forbidden_public_files",
                    [],
                )
            ),
        )

        add_check(
            checks,
            name="stage380_package_integrity_verified",
            passed=(
                stage380.get(
                    "package_integrity_verified"
                )
                is True
            ),
            expected=True,
            actual=stage380.get(
                "package_integrity_verified"
            ),
        )

        add_check(
            checks,
            name="stage380_critical_failure_count_zero",
            passed=(
                stage380.get(
                    "critical_failure_count"
                )
                == 0
            ),
            expected=0,
            actual=stage380.get(
                "critical_failure_count"
            ),
        )

        add_check(
            checks,
            name="stage381_cross_platform_reverification_verified",
            passed=(
                stage381.get(
                    "cross_platform_reverification_verified"
                )
                is True
            ),
            expected=True,
            actual=stage381.get(
                "cross_platform_reverification_verified"
            ),
        )

        add_check(
            checks,
            name="stage381_same_decision_verified",
            passed=(
                stage381.get(
                    "same_decision_verified"
                )
                is True
            ),
            expected=True,
            actual=stage381.get(
                "same_decision_verified"
            ),
        )

        add_check(
            checks,
            name="stage381_same_exit_code_verified",
            passed=(
                stage381.get(
                    "same_exit_code_verified"
                )
                is True
            ),
            expected=True,
            actual=stage381.get(
                "same_exit_code_verified"
            ),
        )

        add_check(
            checks,
            name="stage381_same_stage380_result_sha256_verified",
            passed=(
                stage381.get(
                    "same_stage380_result_sha256_verified"
                )
                is True
            ),
            expected=True,
            actual=stage381.get(
                "same_stage380_result_sha256_verified"
            ),
        )

        add_check(
            checks,
            name="stage381_same_canonical_result_sha256_verified",
            passed=(
                stage381.get(
                    "same_canonical_result_sha256_verified"
                )
                is True
            ),
            expected=True,
            actual=stage381.get(
                "same_canonical_result_sha256_verified"
            ),
        )

        add_check(
            checks,
            name="stage381_critical_failure_count_zero",
            passed=(
                stage381.get(
                    "critical_failure_count"
                )
                == 0
            ),
            expected=0,
            actual=stage381.get(
                "critical_failure_count"
            ),
        )

        critical_failures = sorted(
            check["name"]
            for check in checks
            if (
                check["critical"] is True
                and check["passed"] is False
            )
        )

        if critical_failures:
            decision = "fail_closed"
            verification_status = "invalid"
        elif not stage377_complete:
            decision = (
                "policy_bound_final_acceptance_pending"
            )
            verification_status = (
                "verified_pending_upstream"
            )
        elif not stage378_ready:
            decision = (
                "policy_bound_stage378_reverification_required"
            )
            verification_status = (
                "stage377_complete_stage378_pending"
            )
        else:
            decision = (
                "policy_bound_upstream_finalization_ready_"
                "for_downstream_reverification"
            )
            verification_status = (
                "stage377_and_stage378_complete_"
                "downstream_reverification_required"
            )

        result_without_hash: dict[str, Any] = {
            "stage": STAGE,
            "source_stage": 381,
            "engine": (
                "Stage382 Upstream Finalization Recovery "
                "& Policy Activation Gate"
            ),
            "execution_mode": "development",
            "development_only": True,
            "verification_mode": (
                "upstream_finalization_recovery_"
                "and_policy_activation"
            ),
            "fail_closed": True,
            "formal_acceptance": False,
            "pipeline_completed": False,
            "public_release_allowed": False,
            "policy_profile": {
                "name": policy_profile.get(
                    "profile_name"
                ),
                "version": policy_profile.get(
                    "profile_version"
                ),
                "path": POLICY_PROFILE_PATH.as_posix(),
                "sha256": actual_policy_hash,
                "sha256_record_path": (
                    POLICY_SHA256_PATH.as_posix()
                ),
            },
            "upstream_state": {
                "stage377_result_path": (
                    STAGE377_RESULT_PATH.as_posix()
                ),
                "stage377_result_sha256": (
                    sha256_file(STAGE377_RESULT_PATH)
                ),
                "stage377_decision": (
                    stage377_decision
                ),
                "stage377_verified_proof_count": (
                    stage377_verified_proof_count
                ),
                "stage377_effective_final_acceptance": (
                    stage377_effective_final_acceptance
                ),
                "stage377_complete": stage377_complete,
            },
            "downstream_observation": {
                "stage378_result_path": (
                    STAGE378_RESULT_PATH.as_posix()
                ),
                "stage378_result_sha256": (
                    sha256_file(STAGE378_RESULT_PATH)
                ),
                "stage378_decision": (
                    stage378.get("decision")
                ),
                "stage378_stage377_hash_valid": (
                    stage378.get(
                        "stage377_hash_valid"
                    )
                ),
                "stage378_stage377_final_acceptance_verified": (
                    stage378.get(
                        "stage377_final_acceptance_verified"
                    )
                ),
                "stage378_qkd_metadata_bound": (
                    stage378.get(
                        "qkd_metadata_bound"
                    )
                ),
                "stage378_ready": stage378_ready,
                "stage379_result_sha256": (
                    sha256_file(STAGE379_RESULT_PATH)
                ),
                "stage379_formal_acceptance": (
                    stage379.get("formal_acceptance")
                ),
                "stage379_pipeline_completed": (
                    stage379.get("pipeline_completed")
                ),
                "stage380_result_sha256": (
                    sha256_file(STAGE380_RESULT_PATH)
                ),
                "stage380_package_integrity_verified": (
                    stage380.get(
                        "package_integrity_verified"
                    )
                ),
                "stage381_result_sha256": (
                    sha256_file(STAGE381_RESULT_PATH)
                ),
                "stage381_cross_platform_reverification_verified": (
                    stage381.get(
                        "cross_platform_reverification_verified"
                    )
                ),
                "stage381_common_canonical_result_sha256": (
                    stage381.get(
                        "common_canonical_result_sha256"
                    )
                ),
            },
            "policy_activation_state": {
                "policy_activated": stage377_complete,
                "stage378_reverification_required": (
                    stage377_complete
                    and not stage378_ready
                ),
                "stage378_ready": stage378_ready,
                "downstream_reverification_required": (
                    stage377_complete
                    and stage378_ready
                ),
                "automatic_acceptance_upgrade_performed": False,
                "existing_stage377_evidence_reused": True,
                "new_timestamp_proof_generated": False,
            },
            "decision": decision,
            "verification_status": verification_status,
            "check_count": len(checks),
            "critical_failure_count": len(
                critical_failures
            ),
            "critical_failures": critical_failures,
            "checks": sorted(
                checks,
                key=lambda item: item["name"],
            ),
            "errors": errors,
            "statement": (
                "Stage382 observes Stage377 completion under "
                "a versioned policy. It does not fabricate "
                "upstream completion and does not automatically "
                "upgrade formal acceptance."
            ),
        }

        result_hash = hashlib.sha256(
            canonical_json_bytes(
                result_without_hash
            )
        ).hexdigest()

        result = dict(result_without_hash)
        result["result_sha256"] = result_hash

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT_PATH.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print(f"decision={decision}")
        print(
            "verification_status="
            + verification_status
        )
        print(
            "stage377_verified_proof_count="
            + str(stage377_verified_proof_count)
        )
        print(
            "stage377_effective_final_acceptance="
            + str(
                stage377_effective_final_acceptance
            ).lower()
        )
        print(
            "policy_sha256="
            + actual_policy_hash
        )
        print(
            "critical_failure_count="
            + str(len(critical_failures))
        )
        print(
            "result_sha256="
            + result_hash
        )
        print(
            "result_path="
            + OUTPUT_PATH.as_posix()
        )

        if critical_failures:
            return 2

        return 0

    except (
        FileNotFoundError,
        PermissionError,
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        errors.append(
            f"{type(exc).__name__}: {exc}"
        )

        error_result_without_hash = {
            "stage": STAGE,
            "source_stage": 381,
            "engine": (
                "Stage382 Upstream Finalization Recovery "
                "& Policy Activation Gate"
            ),
            "development_only": True,
            "fail_closed": True,
            "formal_acceptance": False,
            "pipeline_completed": False,
            "public_release_allowed": False,
            "decision": "fail_closed",
            "verification_status": "error",
            "critical_failure_count": 1,
            "critical_failures": [
                "stage382_execution_error"
            ],
            "checks": checks,
            "errors": errors,
        }

        result_hash = hashlib.sha256(
            canonical_json_bytes(
                error_result_without_hash
            )
        ).hexdigest()

        error_result = dict(
            error_result_without_hash
        )
        error_result["result_sha256"] = (
            result_hash
        )

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT_PATH.write_text(
            json.dumps(
                error_result,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print(
            "decision=fail_closed",
            file=sys.stderr,
        )
        print(
            f"error={type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        print(
            "result_path="
            + OUTPUT_PATH.as_posix(),
            file=sys.stderr,
        )

        return 2


if __name__ == "__main__":
    sys.exit(main())
