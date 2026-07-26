# civsim

A constraint-based scenario engine for civilization dynamics.

**Not a predictor.** It rules futures out on physical and accounting grounds,
propagates uncertainty explicitly, and reports where it has no skill. See
[`docs/civilization-simulator-design.md`](docs/civilization-simulator-design.md)
for the feasibility assessment and full design, and
[`docs/model-changelog.md`](docs/model-changelog.md) for every change to model
structure and priors, recorded with whether it was made before or after the
test window was revealed.

Status: **M2** — single-region world model with an explicit technology layer,
inferred per-channel structural error, and rolling-origin evaluation.

---

## Quick start

```bash
pip install -e ".[dev]"

python -m civsim selftest     # conservation + protocol checks, no fitting
python -m civsim backtest     # fit 1950-1990, score 1990-2020, write fan chart
python -m civsim stability    # re-run across seeds; report only robust verdicts
python -m civsim rolling      # four origins; pooled skill + non-stationarity test
python -m civsim rolling --control   # fixed test window; isolates the confound
pytest                        # 49 tests
```

`backtest` writes `out/m2_backtest_fan.png`, plus a run manifest and a protocol
manifest recording the snapshot hash, the freeze, and the reveal.

---

## What M2 actually found

Robust skill on **1 of 9** series (population), across four rolling origins and
four seeds. Everything else is a robust loss or sign-unstable. The `stability`
and `rolling` commands exist so this cannot be reported any other way.

### The model knows how wrong it is, per channel

M1 asserted the model was equally wrong about everything (a uniform 6%
structural scale). Measured, that was off by more than an order of magnitude:

| series | inferred discrepancy | M1 assumed |
|---|---|---|
| low-carbon share | 11–46% | 6% |
| CO₂ emissions | 6.3–9.6% | 6% |
| primary energy | 6.2–9.1% | 6% |
| GDP | 3.7–5.5% | 6% |
| population, CO₂ ppm, age shares | 2.3–4.3% | 6% |

The scale is not assigned per series — that would be fitting the likelihood. It
is given an inverse-gamma prior and integrated out analytically, so each series'
Gaussian becomes a multivariate Student-t. Residuals then enter through
`log(b + Q/2)` instead of `Q`: a badly modelled channel is charged a logarithmic
penalty and reports itself as badly modelled, rather than a quadratic one that
overwhelms every other channel. No sampled parameters added.

**Effect, same five series and seeds, only the likelihood changed:**

| series | M0 | M1 | M2 |
|---|---|---|---|
| population | +49.4% | +12.6% | **+65.0%** robust |
| GDP | −38.5% | −38.7% | −63.0% |
| primary energy | −43.2% | −106.7% | −199.3% |
| CO₂ emissions | −54.6% | −34.1% | −88.9% |
| CO₂ ppm | −451.8% | −81.2% | −83.5% |

Population's robust skill is restored and exceeds M0's. The other channels look
worse, and the reason matters more than the numbers: the likelihood no longer
forces the calibration to chase a channel the model cannot structurally fit, so
it stops distorting shared parameters toward energy. **M1's −107% on energy was
flattered**, bought by degrading population's fit. M2 is not worse at energy;
M2 stopped hiding how bad energy was.

### Non-stationarity, measured rather than asserted

Four origins (1975, 1985, 1995, 2005), each running the full protocol
independently — own prior, own SMC, own freeze, own reveal. Scored points rise
from 6 to 28 per series.

Skill degrades as the origin moves later. That alone is confounded: later
origins have shorter test windows, so the trend could just be three noisy points.
`--control` scores every origin on the *same* 1995–2020 window, moving only the
calibration end — asymmetric in the useful direction, since later origins then
have strictly **more** data.

It still degrades: 6 of 9 series, mean −144 skill points per decade. **Adding
more recent calibration data makes forecasts worse.** First quantitative
confirmation of design §2.2 in this project rather than an appeal to it.

One alternative reading must travel with that finding: more data also tightens
the posterior, and CRPS punishes confident-and-wrong harder than vague. So the
mechanism may be less "the world changed regime" than "a structurally wrong
model given more data becomes more confident without becoming more accurate."
This experiment cannot separate the two, and the second is arguably the sharper
claim.

| series | pooled (18 pts) | 1975 | 1985 | 1995 | verdict |
|---|---|---|---|---|---|
| population | **+63.5%** | +74% | +43% | +74% | **robust skill** |
| useful exergy efficiency | +19.3% | +78% | −71% | −47% | unstable |
| working-age share | +8.5% | +82% | −135% | −499% | unstable |
| GDP | −20.6% | −35% | +57% | −41% | unstable |
| CO₂ ppm | −23.8% | +17% | −150% | −40% | unstable |
| CO₂ emissions | −38.9% | −84% | +70% | +10% | unstable |
| old-age share | −86.5% | −216% | −25% | +50% | unstable |
| primary energy | −138.1% | −120% | −81% | −1087% | robust loss |
| low-carbon share | −425.1% | −66% | −616% | −1281% | robust loss |

### The technology module is still the worst-modelled part

The low-carbon share carries 11–46% structural error and is a robust loss at
every origin. M1 retained the technology layer on the argument that it changes
the reachable set of futures even though it does not improve backtest skill.
That argument still holds and the evidence against the layer is now sharper: it
remains **unfalsified, not validated**, and it is the first thing M3 should
attack.

### Why the ordering mattered

The exergy series added in M2 is C-grade — published estimates disagree on the
level by several points while agreeing on the trend. Adding a series that
uncertain under M1's uniform likelihood would have repeated M1's contamination
exactly. Under the inferred scale it comes out at 3.0–4.9% and neither dominates
nor is ignored. Item 1 is what made item 2 safe.

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
