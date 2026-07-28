# civsim

A constraint-based scenario engine for civilization dynamics.

**Not a predictor.** It rules futures out on physical and accounting grounds,
propagates uncertainty explicitly, and reports where it has no skill. See
[`docs/civilization-simulator-design.md`](docs/civilization-simulator-design.md)
for the feasibility assessment and full design, and
[`docs/model-changelog.md`](docs/model-changelog.md) for every change to model
structure and priors, recorded with whether it was made before or after the
test window was revealed.

Status: **M4** — two-region world model; forward projection, constraint
exclusion, and sensitivity analysis.

---

## Quick start

```bash
pip install -e ".[dev]"

python -m civsim selftest     # conservation + protocol checks, no fitting
python -m civsim backtest     # fit 1950-1990, score 1990-2020, write fan chart
python -m civsim stability    # re-run across seeds; report only robust verdicts
python -m civsim rolling      # four origins; pooled skill + non-stationarity test
python -m civsim rolling --control   # fixed test window; isolates the confound
python -m civsim forward      # project to 2100; what is ruled out, and by what
pytest                        # 56 tests
```

`backtest` writes `out/m3_backtest_fan.png`, plus a run manifest and a protocol
manifest recording the snapshot hash, the freeze, and the reveal.

---

## What M4 actually found

M4 changes direction. Four milestones added mechanism and all cost backtest
skill. Continuing that would be self-justification — and the more likely reading
is already in the design: §1.5's per-variable feasibility table predicted exactly
this. Four rounds of careful mechanism have now confirmed it empirically. **That
is a result, not a failure**, and it means chasing skill is the wrong objective.

Design §7 says the product is four things: probability fans, **the set of paths
ruled out by constraint**, **bifurcation and sensitivity maps**, and an audit
trail. Two had never been built and the model had never been run forward once.
The point of those two is that **neither needs predictive skill.**

### The exclusion analysis found nothing, and that is informative

700/700 posterior draws reach 2100 with no physical limit binding. But over the
*prior*, fossil carbon reserves bind in ~11% of draws (median 2055); over the
posterior, never. So in this model **the binding constraint on emissions is the
low-carbon transition, not running out of fossil carbon** — a statement that
does not depend on any forecast being right.

| target at 2100 | reachable (excluded draws in denominator) |
|---|---|
| CO₂ ≤ 450 ppm | **0.0%** |
| CO₂ ≤ 550 ppm | 37.6% |
| primary energy ≥ 1000 EJ | 73.4% |
| low-carbon share ≥ 50% | 98.9% |
| population ≤ 10 bn | 87.6% |

### A kernel conflation this exposed

Sweeping 120 prior draws, 33 hit a floor on an accounting reservoir and 13 hit
the fossil carbon reserve. Reported together they look like one finding; they are
opposites, and three quarters of it would have been a statement about an
arbitrary constant I had sized by guess. `Limit.PHYSICAL` vs `Limit.RESERVOIR`
now separates them at the type level — exhausting a reserve is counted as data,
exhausting a reservoir raises a distinct exception that calls itself a bug.

### What the spread actually turns on

| outcome at 2100 | top drivers |
|---|---|
| population | `fert_half` +2.06 |
| GDP | `tfp_elasticity` +0.84, `fert_half` +0.77 |
| primary energy | `energy_service_theta` +0.77 |
| CO₂ ppm | `energy_service_theta` +0.78, `learning_rate_modular` −0.54 |

The largest single lever on 2100 concentration is the **shape of the energy
service ladder**, not the learning rate — demand-side saturation ahead of
supply-side learning. Not what the technology literature would suggest, and
exactly the kind of claim to check with a real Sobol decomposition before acting
on. (These are standardised regression coefficients, which understate
interaction.) `fert_half` appears in three of four rows: demography is the
dominant uncertainty even for carbon outcomes.

---

## What M3 found

Robust skill on **1 of 13** series (population, +33.7% across seeds). Everything
else is a robust loss or sign-unstable.

### The trade-off M3 forced into the open

The first two-region build had the **lagging region's capital per head overtake
the leader's** by 2020 (ratio 4.41 → 0.88). A shared global technology frontier
plus Solow accumulation drives full convergence and then overshoot. Fixed with
absorptive capacity (design §8, L3): a region captures the frontier only to the
extent its own development lets it. Overshoot gone — 0 of 38 draws cross over.

And it made the backtest worse:

| | without absorption | with absorption |
|---|---|---|
| robust skill | 2/13 | **1/13** |
| high-income GDP share | **+40.6%** robust skill | −73.7% robust loss |
| population | +44.1% | +33.7% |

The no-absorption version fitted the observed 1950–2020 convergence of the income
split **by over-converging**, and paid for it with an absurd extrapolation
starting just past the scored window. The parameters that reproduce historical
catch-up imply overshoot afterwards; the model can do one or the other.

**The absorption version ships**, for the same reason M1's technology layer did:
hold-out skill over 1950–2020 cannot see an overshoot that begins in 2020, and a
model where poor regions overtake rich ones is unusable for every forward
question this project exists to ask.

### Errors are correlated across channels, and now counted once

M2 scored each series independently. Emissions are computed *from* energy here,
so that counted one error twice. The residual matrix is now modelled with a
separable covariance and an inverse-Wishart prior integrated out, giving a
matrix-t whose key term is a **determinant** rather than a sum of per-series
penalties: aligned residuals stop being separate evidence.

Measured error correlations:

| pair | correlation |
|---|---|
| energy ↔ emissions | **+0.92** |
| emissions ↔ GDP | +0.73 |
| energy ↔ GDP | +0.66 |

Likelihood discrimination fell from 105 to 89 nats — the correct direction, since
the extra sharpness was an artefact.

### Two low-carbon technology families

The observed low-carbon share rises, sits on a twenty-year plateau (11.3% in 1990
→ 12.6% in 2010), then resumes. One family with one learning curve cannot produce
that at any parameter value. Split into dispatchable (hydro/nuclear: slow
learning, hard ceiling) and modular (wind/solar: steep learning, tiny base), the
plateau emerges as the gap between one saturating and the other arriving. Prior
draws producing that shape went from 0% to 4%. Inferred discrepancy on the
channel improved from 11–46% to 21.5% — still the worst channel by a factor of
two.

### A prediction designed to fail

Technology is global in M3, so `hi_co2_share` must equal `hi_energy_share`
exactly. Observation says 38% of energy but 33% of CO₂ in 2020. It is scored
anyway and fails (−200%). The gap measures how much regional technology
heterogeneity matters — worth more than omitting a prediction the model is
committed to making.

### Four milestones in

The model has robust skill on exactly one variable, and it is the one design §3.1
predicted for the reason §3.1 gave: cohort inertia. Every added mechanism has
been structurally necessary and has cost backtest skill. The design's §15.1 merge
rule has now been overridden three times on the same argument — that reachable-set
coherence is not measurable by hold-out skill. If that argument is wrong, the last
three milestones were a mistake, and nothing in the backtest can settle it.

---

## Architecture

```
civsim/
  core/        SFC kernel: stocks, paired flows, conservation ledger,
               sectoral financial ledger, explicit-Euler engine
  data/        A/B/C-graded snapshot registry with content hashing
  modules/     pop_R -> technology -> energy_R -> economy_R -> aggregate -> carbon
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
