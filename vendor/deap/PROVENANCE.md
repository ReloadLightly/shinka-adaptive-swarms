# DEAP source provenance

Upstream repository: https://github.com/DEAP/deap

Pinned commit: `8a96fd3a75026f7b30e835f595a5199c75634ddf`
(2026-04-17, upstream commit message: Bump version to 1.4.4).
Retrieved through the GitHub file API on 2026-09-15.

| Local file | Upstream path | Git blob SHA |
|---|---|---|
| `movingpeaks.py` | `deap/benchmarks/movingpeaks.py` | `42c174a5a85ec4fe3cc32c1243e89ed4bf9526c2` |
| `multiswarm.py` | `examples/pso/multiswarm.py` | `a799d0a143c656dd2cf79c2bc89a6cdc79a30796` |
| `COPYING.LESSER` | `LICENSE.txt` | `cca7fc278f5c81ce23a2687208f0d63a6ea44009` |

These three files are byte-for-byte copies. Verify them with:

```bash
git hash-object vendor/deap/movingpeaks.py vendor/deap/multiswarm.py vendor/deap/COPYING.LESSER
```

The Python file headers license them under GNU LGPL version 3 or later.
`COPYING.LESSER` contains the upstream LGPL text. `COPYING` contains the
complete GPL version 3 text incorporated by LGPL3, copied from the runtime's
`/usr/share/common-licenses/GPL-3`. Upstream copyright and license headers
are preserved.

`movingpeaks.py` is imported directly by the simulator without modification.
`multiswarm.py` is retained as source evidence, **not executed as the research
baseline**: its quantum-distribution selector is overwritten by a numerical
norm, making all relocation branches unreachable. The project optimizer in
`src/adaptive_swarms/simulator.py` implements corrected UVD sampling and the
book's attractor reevaluation. See `docs/reproduction.md` for deviations.

Permanent source links:

- https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/deap/benchmarks/movingpeaks.py
- https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/pso/multiswarm.py
- https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/LICENSE.txt
