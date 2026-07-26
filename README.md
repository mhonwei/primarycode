# civsim

A constraint-based scenario engine for civilization dynamics.

**Not a predictor.** It rules futures out on physical and accounting grounds,
propagates uncertainty explicitly, and reports where it has no skill. See
[`docs/civilization-simulator-design.md`](docs/civilization-simulator-design.md)
for the feasibility assessment and full design, and
[`docs/model-changelog.md`](docs/model-changelog.md) for every change to model
structure and priors, recorded with whether it was made before or after the
test window was revealed.

Status: **M1** — single-region world model with an explicit technology layer,
1950–2020 backtest.

---

## Quick start

```bash
pip install -e ".[dev]"

python -m civsim selftest     # conservation + protocol checks, no fitting
python -m civsim backtest     # fit 1950-1990, score 1990-2020, write fan chart
python -m civsim stability    # re-run across seeds; report only robust verdicts
pytest                        # 44 tests
```

`backtest` writes `out/m1_backtest_fan.png`, plus a run manifest and a protocol
manifest recording the snapshot hash, the freeze, and the reveal.

---

## What M1 actually found

Calibrate 1950–1990, freeze, then score 1990–2020 against five naive baselines
(random walk, drifting random walk, log-linear trend, AR(1) on growth, recent
trend). CRPS, model and baselines scored like-for-like — every baseline carries
its own fitted uncertainty, so the comparison is not rigged toward the
probabilistic model. Verdicts are those whose sign survives four seeds; a
single-run skill number is not reported as a result.

**M1 has robust skill on zero series. M0 had one.** Measured on M0's own five
series so the comparison is like-for-like:

| series | M0 mean | M1 mean [min, max] | verdict |
|---|---|---|---|
| population | **+49.4%** | +12.6% [−57, +63] | robust skill lost, now unstable |
| GDP | −38.5% | −38.7% [−79, −15] | robust loss, unchanged |
| primary energy | −43.2% | **−106.7%** [−182, −19] | robust loss, materially worse |
| CO₂ emissions | −54.6% | −34.1% [−74, +15] | improved, sign unstable |
| CO₂ concentration | −451.8% | **−81.2%** [−191, +36] | hugely improved, still a net loss |

Two things went right and two went wrong, and they are separable.

**The land-use fix worked, exactly as M0's residuals predicted.** Concentration
was M0's worst failure by a factor of eight; adding the missing source term
moved it from −452% to −81%. The diagnosis that too-high emissions with
too-low concentration means a *missing source* rather than a wrong parameter
was correct and led straight to the fix. Caveat that must travel with it: the
frozen run tracks concentration to 0.5% MAPE while running fossil emissions 23%
high, so the calibration is offsetting a too-steep emissions path with a high
uptake coefficient. The carbon module is less wrong, not right.

**The technology module made energy substantially worse** (−43% → −107%, robust
across every seed). Energy demand now has two opposing mechanisms — a service
ladder rising with development, efficiency knowledge pushing the other way —
where M0 had one exponential, and aggregate primary energy cannot separate them.
Any pair that fits 1950–1990 is admitted, and they diverge afterwards. Adding a
mechanism that is not separately observable made the forecast worse. The fix is
not a better prior but data that identifies the channels, which means sectoral
intensity series and belongs to M2.

**The age-structured population lost M0's one robust win** (+49% → +13%). Three
Erlang-staged compartments are more realistic than one aggregate stock and
forecast worse.

### By this project's own merge rule, the technology module fails

Design §15.1 says every new subsystem must demonstrate it improved the hold-out
score before being merged. On backtest evidence, neither the technology module
nor the age structure does.

**Both are retained anyway, and the reason is on the record rather than
assumed.** M0's diagnosis was that an emissions plateau lay outside its reachable
set *at every parameter value*. That is a statement about which futures the model
can represent, and backtest skill over 1950–2020 cannot measure it — a model can
track history well while being structurally incapable of the transition every
forward scenario turns on. The technology layer changes the reachable set, which
is what a scenario generator needs and what §15.1 was not written to weigh.

The consequence: **the technology module is currently unfalsified, not
validated.** It has earned a claim to be necessary, not a claim to be right.
Those must not be conflated.

### Conservation is necessary and not sufficient

Two M1 defects passed every conservation check:

- **Diffusion deadlock.** Learning needs deployment, deployment needs cost
  parity, cost parity needs learning. The low-carbon share fell from 2.5% to
  0.03% over seventy years while retirement ate capacity that was never
  replaced — a technology module that could not represent any transition. Fixed
  with a niche deployment floor (hydro, plus the policy demand that historically
  bought nuclear and solar learning above market price). `lowcarbon_share_pct` is
  now a scored series so the layer is falsifiable on its own terms.
- **Negative conversion efficiency.** When knowledge fell below its t0 index the
  exponent flipped sign, useful work went negative, and the CES bracket returned
  a *complex number* that propagated silently until something compared it to
  zero. Nothing was created or destroyed, so the ledger saw nothing.

Quantities with physical ranges need their ranges asserted separately from their
balances. Both now have regression tests.

---

## Architecture

```
civsim/
  core/        SFC kernel: stocks, paired flows, conservation ledger,
               sectoral financial ledger, explicit-Euler engine
  data/        A/B/C-graded snapshot registry with content hashing
  modules/     population -> technology -> energy -> economy -> carbon
  uncertainty/ priors, tempered SMC, correlated-discrepancy likelihood
  backtest/    hold-out gate, baselines, CRPS/PIT scoring, runner
  viz/         fan charts with credible-horizon greying
```

### The kernel

Every flow moves one conserved quantity from a **named source stock** to a
**named sink stock**. There is no flow without a source. Modules never write
state — they return rates, and the engine applies them — so "emissions appeared
from nowhere" is a conservation failure rather than an invisible assumption.
Boundary stocks (unextracted fossil carbon, the not-yet-born, dissipated heat)
make the model's edges explicit.

Carbon and energy are conserved by physics; capital and money by accounting
identity. The distinction is recorded per quantity, because it determines what a
violation means. `tests/test_conservation.py` constructs modules that each
commit a specific sin and asserts the engine refuses them.

### The hold-out gate

Test data is behind a gate, not behind good intentions. `Holdout.calibration()`
is always readable; `reveal_test()` raises until `freeze()` has been called;
`assert_fit_allowed()` raises after reveal. This makes the mechanical version of
§11.1 impossible and forces the judgement version into the changelog.

It does not solve hindsight leakage (§2.6) — the author already knows what
1990–2020 looked like, and that knowledge leaks through every choice of
functional form. Nothing in code fixes that; the changelog is what makes it
weighable.

### Two sampler bugs worth knowing about

Both were found and fixed before the reveal, and both would have produced
confident-looking empty results:

- **Independent-by-year likelihood.** Scoring each calendar year as an
  independent observation overstates the information in a smooth 40-year series
  by roughly an order of magnitude. Nine 5-yearly points are worth about 1.7
  independent observations under a 25-year discrepancy correlation length.
- **Prior importance sampling.** At 24 free parameters it collapses to a single
  particle (ESS 1.0 of 3000; best draw beat second best by 13 nats). The "fan
  chart" was one trajectory drawn 3000 times. Replaced with adaptive tempered
  SMC — now 95% unique particles, acceptance 21–34%, 7 tempering stages.

The two were independent: fixing the likelihood did **not** raise ESS above 1.0.

---

## Data

Bundled snapshot of world aggregates 1950–2020 (5-yearly), content-hashed and
committed. Remote fetchers are wired but optional — the snapshot is the primary
artefact, because a model whose backtest score moves when someone else
re-estimates 1950 is not measuring its own skill.

Every series carries source, citation, and an A/B/C grade that can vary by era
(atmospheric CO₂ is B-grade ice core before 1959, A-grade Mauna Loa after).
Grade drives the observation term of the likelihood and travels with any result.

---

## Known limitations in M1

- **Energy channels are unidentified.** The service ladder and the efficiency
  knowledge stock are not separately observable in aggregate primary energy.
  This is the direct cause of the energy regression and needs sectoral data.
- **The likelihood assigns every series the same 6% structural scale.** A series
  the model fits at 27% MAPE then dominates the joint likelihood and contaminates
  parameters shared with series it could fit well. Most likely single cause of
  the population regression; should be estimated per series, not assigned.
- **Six scored points cannot resolve skill.** Rolling-origin scoring across
  several cutoffs would raise the point count and test non-stationarity directly.
- Three age compartments, not single-year cohorts. Cohorts need ~40 more
  parameters against nine 5-yearly aggregate observations; M1 is what happens
  when mechanism outruns identifiability, and doing it again deliberately would
  be a decision to produce noise.
- Single region. No trade, no geopolitics, no heterogeneity.
- The carbon reduced form ties fast uptake to gross emissions, so it **cannot be
  trusted under net-negative emissions**. Any carbon-removal scenario needs a
  real impulse-response model.
- Explicit Euler at dt=1yr. First-order, and deliberately so: adaptive
  integration would buy accuracy the 5-yearly grade-B inputs do not support
  while making exact conservation bookkeeping much harder.
- Energy reserves are set large enough not to bind. Making depletion bite is M2.
