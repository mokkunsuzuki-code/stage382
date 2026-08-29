# Stage382: Upstream Finalization Recovery & Policy Activation Gate

日本語：

# 上流最終確定回復・ポリシー有効化ゲート

Stage382 extends Stage381 without replacing or rewriting the established
Stage377 through Stage381 verification history.

Stage382 observes the completion state of Stage377 under a fixed,
versioned policy profile. It remains Fail-Closed while Stage377 is
incomplete and requires downstream reverification after Stage377 reaches
its required final-acceptance state.

## Purpose

Stage382 has four primary purposes:

1. Preserve the existing Stage377 timestamp evidence
2. Bind the Stage377 completion requirements to a versioned policy
3. Detect when Stage377 satisfies the required dual-timestamp conditions
4. Require Stage378, Stage379, Stage380, and Stage381 reverification after activation

Stage382 does not create a replacement OpenTimestamps proof and does not
weaken the existing Stage377 requirements.

## Verification Flow

```text
Existing Stage377 evidence
        |
        v
Versioned policy profile validation
        |
        v
Policy SHA-256 validation
        |
        v
Stage377 completion observation
        |
        +---- incomplete ----> Fail-Closed pending state
        |
        v
Stage378 reverification required
        |
        v
Stage379 reverification required
        |
        v
Stage380 reverification required
        |
        v
Stage381 cross-platform reverification required
        |
        v
Stage382 policy-bound result
```

## Current State

The finalized Stage377 result reports:

```text
decision:
dual_timestamp_final_acceptance_verified

verified_proof_count:
2

effective_final_acceptance:
true
```

The independently audited Stage378 final run reports:

```text
run:
33075729675

decision:
qkd_operational_evidence_pending

stage377_final_acceptance_verified:
true

stage377_hash_valid:
true

stage377_verified_proof_count:
2

qkd_metadata_bound:
true

evidence_classification:
metadata_only

evidence_level:
QKD-E1
```

Stage382 now reports:

```text
decision:
policy_bound_upstream_finalization_ready_for_downstream_reverification

verification_status:
stage377_and_stage378_complete_downstream_reverification_required

critical_failure_count:
0

stage378_reverification_required:
false

stage378_ready:
true

downstream_reverification_required:
true

formal_acceptance:
false

pipeline_completed:
false

public_release_allowed:
false
```

Stage378 is complete for its declared `metadata_only` / `QKD-E1`
verification scope.

`qkd_operational_evidence_pending` means that operational QKD evidence
has not been claimed. It does not mean the Stage378 metadata binding
failed.

Stage379, Stage380, and Stage381 still require downstream
reverification.

## Versioned Policy Profile

Stage382 currently uses one policy profile:

```text
qsp-dual-timestamp-final-acceptance-v1
```

Profile version:

```text
1.0.0
```

Policy SHA-256:

```text
1819dc41cee56da7f7faabdbdc6dab44326054c9197bf5bd6c52286b7e8e9ea5
```

The policy requires:

- two verified timestamp proofs
- RFC3161 verification
- OpenTimestamps verification
- the same Stage360 target binding
- no pending timestamp proof for final acceptance
- reuse of the existing OpenTimestamps proof
- no replacement proof generation
- Fail-Closed enforcement
- no scope reduction

## Stage377 Activation Conditions

Policy activation requires:

```text
verified_proof_count == 2
effective_final_acceptance == true
```

After Stage377 completes, Stage382 requires the audited Stage378 final
evidence to remain bound to that finalized Stage377 result before
downstream reverification may proceed.

Current transition:

```text
Stage377 complete
        |
        v
Stage378 final/run-33075729675 validated
        |
        v
Stage377 -> Stage378 canonical binding verified
        |
        v
policy_bound_upstream_finalization_ready_for_downstream_reverification
        |
        v
Stage379 reverification required
        |
        v
Stage380 reverification required
        |
        v
Stage381 cross-platform reverification required
```

No downstream stage is automatically upgraded.

## Fail-Closed Tests

Stage382 currently has 11 Fail-Closed tests covering:

- completed Stage377 and Stage378 allowing downstream reverification
- completed Stage377 requiring Stage378
- the current finalized upstream state
- incomplete Stage377 not being upgraded
- incomplete Stage377 combined with finalized Stage378 failing closed
- missing required evidence files
- policy SHA-256 tampering
- Stage378 publication-boundary violations
- Stage377-to-Stage378 binding mismatch
- Stage380 package-integrity failure
- Stage381 cross-platform reproducibility failure

The tests operate on temporary copies and do not modify the actual
Stage377 through Stage381 records.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 \
python3 development/stage382/test_stage382_fail_closed.py
```

## Run the Stage382 Verifier

```bash
PYTHONDONTWRITEBYTECODE=1 \
python3 development/stage382/verify_stage382_upstream_finalization.py
```

Current expected result:

```text
decision=policy_bound_upstream_finalization_ready_for_downstream_reverification
verification_status=stage377_and_stage378_complete_downstream_reverification_required
stage377_verified_proof_count=2
stage377_effective_final_acceptance=true
critical_failure_count=0
```

Current embedded Stage382 result SHA-256:

```text
2785ea5f496dc3d882467ea727d5adf17b5276491d9b31a098fd697f5c9da8ac
```

The verifier remains deterministic for the current fixed input set.

## Public Verification Files

Stage382 public development files include:

```text
development/stage382/
├── README.md
├── policy-profiles/
│   ├── qsp-dual-timestamp-final-acceptance-v1.json
│   └── qsp-dual-timestamp-final-acceptance-v1.sha256
├── verify_stage382_upstream_finalization.py
├── test_stage382_fail_closed.py
├── stage382_upstream_finalization_result.json
├── stage382_upstream_finalization_result.sha256
├── stage382_policy_activation_manifest.json
└── stage382_policy_activation_manifest.sha256
```

## Preservation Boundary

Stage382 does not modify or overwrite:

- Stage377 timestamp-finalization result
- Stage378 QKD metadata-binding result
- Stage379 scoped verification result
- Stage380 independent verification result
- Stage381 cross-platform verification result

Stage382 only observes, verifies, hashes, binds, and reports the current
state.

## Security and Publication Boundary

The following material must not be published:

```text
core/
private_core/
private/
secrets/
keys/
imported/
```

Stage382 also prohibits publication of:

- private keys
- credentials
- authentication tokens
- raw QKD secret material
- raw timestamp binary proofs
- confidential execution material
- private-core implementation material

Only reviewed public metadata, policy files, source code, SHA-256 records,
and verification results may be published.

## Formal-Acceptance Boundary

Stage382 is currently development-only.

The following values remain false:

```text
formal_acceptance = false
pipeline_completed = false
public_release_allowed = false
```

A successful policy-integrity check is not equivalent to production
formal acceptance.

A completed Stage377 state is not automatically equivalent to completed
Stage379 through Stage381 reverification.

## License

This Stage382 public source code and documentation are licensed under the
MIT License.

See the repository-level `LICENSE` file for the complete license text.

The MIT License does not override confidentiality requirements, security
controls, private-material restrictions, third-party licenses, or the
publication boundary defined by this project.
