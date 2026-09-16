# Radius / velocity sprint archive

Completed exploratory diagnostic, native discovery and frozen pilot.
Read [the report](../../../docs/sprints/radius_velocity_20260916/REPORT.md), [accounting.json](accounting.json), and the
[pilot selection freeze](pilot_selection.json). All sixteen pilot methods/cases
and all development cases remain, including large losses.

- `phase_a`: six methods, eight paired development histories each.
- `evolution/search_seed_620001`: thirteen valid native slots including the cached seed,
  twelve valid descendants, exact sources/lineage, feedback, role receipts and logs.
- `pilot`: two frozen methods on eight fresh paired histories.
- `programs/pilot_selected.py`: exact selected constant radius1.25/retain rule;
  the adapter fixes count four and memory reevaluation.
- `operations`: timestamped evidence, independent audits, browser/source checks.
- `ARCHIVE.json`: byte-copy/consistent-SQLite provenance and exclusions.
- `MANIFEST.json`: payload sizes and SHA256 inventory (excluding itself).

Research used160 full executions/16Mqueries; eight seed reuses and eight counted
repeated descendant executions are distinguished. Small fixtures used14,000queries.
Native logical responses45/60:13mutation,13novelty,19meta. No paid fallback.

Original execution paths are provenance. Saved-data analysis works from this
archive using `scripts/analyze_radius_velocity_sprint.py --run <archive> --phase-a`
or `--pilot`, with `--output /tmp/<new-directory>` to preserve archive files.
Serve the native database with `bash scripts/webui.sh <archive>/evolution 8894`
only if that port is not already serving the live local run.
