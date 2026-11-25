# Hugging Face benchmark data feasibility

Related to #5. Evidence reviewed 2026-11-25. Status: partially verified; not an ingestion or scoring implementation.

## Access and evidence

Hugging Face documents a dataset-centric leaderboard endpoint (GET https://huggingface.co/api/datasets/{dataset_id}/leaderboard), model-centric evaluation metadata, and the OpenEvals/leaderboard-data aggregate Parquet dataset. Public data may be accessible without credentials; gated data requires authorized access. Do not automatically request credentials or change data sources on failure.

| Source | Observed status | Revision and rights |
| --- | --- | --- |
| SWE-bench/SWE-bench_Verified | Public leaderboard JSON and dataset page retrieved through web tooling; cached snapshot, approximately three months old, not current inventory. | Exact dataset and evaluation revisions not established; score reuse and attribution review open. |
| harborframework/terminal-bench-2.1 | Dataset and leaderboard API retrieval unsuccessful; no current response inspected. Official upstream documentation confirms a separate 2.1 benchmark and leaderboard. | Revision and rights not verified. |
| harborframework/terminal-bench-2-leaderboard | Public repository listing and historical README inspected. Contains agent/model submissions and job artifacts rather than a small unified API response. | Listing labels Apache-2.0; historical README at dcfb47ed59980473bea884bf8321a87cb9a3e285. This does not establish rights to every linked or embedded artifact. |
| OpenEvals/leaderboard-data | Official HF documentation describes aggregated scores; retrieval returned 429. | Schema, freshness, coverage, exact revision and rights not verified. |

No task content, execution logs, credentials or raw leaderboard records are copied into this repository.

## Observed leaderboard structure

The SWE-bench Verified JSON sample contains rank, modelId, value, verified, source, filename, pullRequest, lower_is_better, and additional metadata. Optional notes can describe the evaluation setup. Use source-native field names at the adapter boundary (SDK names may differ). Sample entries include DeepSeek V4 Pro and MiniMax M3; both are marked unverified in the retrieved snapshot. This demonstrates availability of candidate evidence, not an exact match to a configured OpenCode model or current default effort. SWE-bench Verified measures the proportion of resolved software issues; the dataset page shows 500 test rows. Do not treat ranking position as a score.

HF's evaluation format supports dataset ID, task ID, optional dataset revision, score, date, verification token, source and notes. Its verification badge has a particular meaning in that system; preserve source-native status and evidence rather than interpreting it as universal independent replication. A missing revision, effort or harness cannot be assumed to match the desired configuration.

## Comparability

- SWE-bench results measure a model plus execution environment. The official leaderboard distinguishes unrestricted system submissions from a common mini-SWE-agent bash-only setup. Prefer comparable same-harness results where available; never compare arbitrary systems as if measuring a model alone.
- Terminal-Bench 2.1 revises tasks from 2.0; keep versions separate. The upstream submission instructions include agent, model, effort and repeated trials. The legacy HF submission repository is large and is not a suitable full mirror for the MVP. Do not infer benchmark version from a directory name alone.
- Preserve original model identifiers, source, evaluation date, revision, harness/version, effort, metric/unit/direction, trial count where available, verification status and attribution. Unknown values remain unknown. Multiple conflicting runs remain separate evidence; selection policy requires a separate scoring decision.
- Public benchmark scores are not measured performance of the user's own agent team. Unknown preview and contributor models remain selectable subject to mandatory policies, but unranked when comparable evidence is insufficient. Optional practical tests under #2 remain separate.
- Cross-source duplicate detection must consider the underlying run and not count the same score twice simply because multiple aggregators list it.
- No full selected-model coverage percentage can be supported by this partial, cached evidence.

## Suggested MVP scope

Start with explicitly selected public SWE-bench Verified leaderboard evidence as a candidate supplementary source. Keep Terminal-Bench and OpenEvals as pending validation, not automatic fallbacks. Use a small versioned benchmark registry, read-only public requests, local caches with provenance and freshness, and explicit manual import of authorized score records. Fetch only relevant score metadata; do not download benchmark task collections, model weights or run benchmark workloads. Fail closed on request failures; new attempts or alternative sources require explicit user choice. Use synthetic fixtures in tests until source reuse conditions are settled.

## Reproduction and remaining gates

Open the official leaderboard endpoint without a token for a public dataset. Inspect returned JSON field names and source/verification metadata. Resolve benchmark and evaluation revisions from the upstream dataset/model repositories where available. Retrieve the same requested Terminal-Bench endpoint and aggregate metadata separately when available; report failures without bypassing limits. Check access/terms and attribution before storing or redistributing real records. Verify exact model/version/default-effort mapping against the actual selected native routes before scoring. No paid requests or model executions were performed in this spike. Keep #5 open pending these checks.

## Sources

- https://huggingface.co/docs/hub/leaderboard-data-guide
- https://huggingface.co/docs/hub/eval-results
- https://huggingface.co/api/datasets/SWE-bench/SWE-bench_Verified/leaderboard
- https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified
- https://www.swebench.com/verified
- https://huggingface.co/api/datasets/harborframework/terminal-bench-2.1/leaderboard (retrieval unsuccessful)
- https://github.com/harbor-framework/terminal-bench-2-1
- https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/tree/main
- https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/blob/dcfb47ed59980473bea884bf8321a87cb9a3e285/README.md
- https://huggingface.co/datasets/OpenEvals/leaderboard-data (429 on retrieval)
