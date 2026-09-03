# E4D1D3P0 F1 — canonical 2019 schema-authority rebinding

The P0 precommit itself was committed successfully. Its static inspector then failed before producing any P0 outputs because it treated `E4D1BR_2019_schema_audit_registry.tsv` as the current ACS compatibility authority and required its ACS row to be PASS.

That registry is intentionally historical. It records the earlier blocked state where ACS was FAIL. The project subsequently executed a precommitted sequence of targeted structural repairs, ending in E4D1BR2CR0. The final CR0 artifacts freeze ACS as VERSIONED_PASS, SCF and CPS_ASEC as PASS, overall schema as PASS_WITH_VERSIONED_BRIDGE, and the version bridge as VALIDATED_FROZEN.

E4D1C later consumed these exact CR0 artifacts as the canonical prerequisite before authorizing the 2019 coordinate precommit.

F1 does not rerun or reinterpret the ACS structural repair. It only rebinds the P0 static inspector from the stale historical registry to the exact final CR0 schema, decision and bridge bytes.

The parent P0 plan, staged execution order and scientific method are unchanged. No raw 2019 row or coordinate value is opened.
