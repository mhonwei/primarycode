# civsim

A constraint-based scenario engine for civilization dynamics.

**Not a predictor.** It rules futures out on physical and accounting grounds,
propagates uncertainty explicitly, and reports where it has no skill. See
[`docs/civilization-simulator-design.md`](docs/civilization-simulator-design.md)
for the feasibility assessment and full design, and
[`docs/model-changelog.md`](docs/model-changelog.md) for every change to model
structure and priors, recorded with whether it was made before or after the
test window was revealed.

Status: **M0** — single-region world model, 1950–2020 backtest.

---

## Quick start

```bash
pip install -e ".[dev]"

python -m civsim selftest     # conservation + protocol checks, no fitting
python -m civsim backtest     # fit 1950-1990, score 1990-2020, write fan chart
python -m civsim stability    # re-run across seeds; report only robust verdicts
pytest                        # 41 tests
```

`backtest` writes `out/m0_backtest_fan.png`, plus a run manifest and a protocol
manifest recording the snapshot hash, the freeze, and the reveal.

---

## What M0 actually found

Calibrate 1950–1990, freeze, then score 1990–2020 against five naive baselines
(random walk, drifting random walk, log-linear trend, AR(1) on growth, recent
trend). CRPS, model and baselines scored like-for-like — every baseline carries
its own fitted uncertainty, so the comparison is not rigged toward the
probabilistic model.

Verdicts below are those whose sign survives five independent seeds. A
single-run skill number is **not** reported as a result: GDP skill came out
+5.7% with 1200 particles and −14.7% with 1500, on six scored points.

| series | skill vs best baseline | verdict |
|---|---|---|
| world population | +49% (+12% … +72%) | **robust skill** |
| world GDP | −39% (−93% … +7%) | sign unstable — no demonstrated skill |
| primary energy | −43% (−97% … −3%) | robust loss |
| CO₂ emissions | −55% (−132% … −20%) | robust loss |
| atmospheric CO₂ | −452% (−478% … −404%) | robust loss |

**One win out of five.** The three robust losses have identified structural
causes, documented in the changelog:

1. **Land-use-change emissions are omitted.** Concentration runs 4.5% low while
   emissions run 30% high — a combination no parameter error can produce. The
   uptake coefficient was calibrated against a carbon budget that counts fossil
   *plus* land use; the model is fed fossil only.
2. **Energy demand cannot decouple.** Tracks observation to +1.8% at 1990, then
   diverges monotonically to +24.7% by 2020. Demand is anchored to the capital–
   labour composite with a fixed drift; the post-1990 world decoupled and the
   model has no mechanism that can express a regime change in intensity. This
   is design §2.2 (non-stationarity) appearing on the first run.
3. **Emissions cannot plateau.** Observed emissions flatten 2015–2020; carbon
   intensity declines at a fixed exponential rate, so a plateau is outside the
   model's reachable set at any parameter value.

None of these has been fixed, because they were identified *after* the test
window was revealed. Fixing them now would be tuning against a revealed test
set. They are the M1/M2 agenda, to be re-frozen and re-scored from scratch.

Design §5 predicted energy would beat baselines and GDP would not. Both calls
were wrong, in opposite directions — §5 reasoned about whether a variable is
predictable *in principle* and never asked whether this model contains a
mechanism capable of predicting it. Those are separate claims.

---

## Architecture

```
civsim/
  core/        SFC kernel: stocks, paired flows, conservation ledger,
               sectoral financial ledger, explicit-Euler engine
  data/        A/B/C-graded snapshot registry with content hashing
  modules/     population -> energy -> economy -> carbon
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

## Known limitations in M0

Beyond the three structural failures above:

- Aggregate population, not cohorts. Crude death rate is monotone decreasing in
  development, so ageing cannot turn it back up — the model **understates**
  deaths late in the run, and its population path is an upper envelope. Cohorts
  are M1.
- Single region. No trade, no geopolitics, no heterogeneity.
- The carbon reduced form ties fast uptake to gross emissions, so it **cannot be
  trusted under net-negative emissions**. Any carbon-removal scenario needs a
  real impulse-response model.
- Explicit Euler at dt=1yr. First-order, and deliberately so: adaptive
  integration would buy accuracy the 5-yearly grade-B inputs do not support
  while making exact conservation bookkeeping much harder.
- Energy reserves are set large enough not to bind. Making depletion bite is M2.
