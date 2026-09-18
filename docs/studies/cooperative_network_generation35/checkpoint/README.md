# Final generation-35 checkpoint

This is the byte-identical final checkpoint from source commit `42ccaaf4b4f9c361f671cf54b6d874bc4d442359`.

- [programs-036.sqlite](programs-036.sqlite): SHA256 `a9ea1ab968feb284d92d18c8191bb977086209cdf3968b88b73a517245935106`.
- [Matching native continuation state](native-036/): bandit state, task identity,
  prompt database, meta state and meta export; original per-file hashes remain in
  the [drained verification receipt](operations/generation-35-drained-verification.json).
- [Original campaign manifest](../source/campaigns/paper_trajectory_v2.json),
  [review target](review-target.json) and [pause receipt](pause-request.json).

The stored record fingerprint is `da9979f9be831520db19fc3672adc1bab9f8c6606c4aea26bd879685e2caab92`.
It was established by the source publication workflow; this compact assembly checks
byte hashes against that receipt and the SQLite integrity, rather than rerunning the
scientific export verification. The database preserves the population, lineage,
islands and archive. Matching native state preserves bandit, prompt and meta memory,
including the pending G32–35 buffer. Counts are 35 descendant proposals, 32 valid,
three failed/invalid slots, and one seed placed on three islands. No unfinished
accepted job or proposal 36 exists at this checkpoint.

**Paused after generation-35 review; further discovery and fresh confirmation await a subsequent decision.**

This is a compact publication of the checkpoint, not a complete restoration kit.
Full evaluation caches, trajectory files, usage journals, provider receipts and
runtime dependencies remain in the [pinned original study](https://github.com/ReloadLightly/shinka-cooperative-network/tree/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/).
Retained metadata contains original source-workspace paths; [PROVENANCE.json](../PROVENANCE.json)
maps the included paths without changing checkpoint bytes. Do not launch a new
campaign from this directory or assume omitted caches have been transferred.
