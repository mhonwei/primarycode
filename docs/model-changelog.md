# Model changelog

Required by design §11.7. Every change to model structure or priors is recorded
here, **with whether it was made before or after the test window was revealed**.

The distinction is the whole point. A change made before the reveal is ordinary
model development. A change made after it is a change made by someone who knows
the answer, and no amount of good faith makes it otherwise — it can only be
justified structurally (a mechanism that is missing is missing regardless of
which way it moves the score), never by "it fits better now".

Format: date · change · **when** · justification.

---

## M0 — 2026-07-26

### Pre-reveal changes

**Prior recentred: `energy_per_kl_growth` from `N(-0.005, 0.004)` to `N(0, 0.005)`**
· *before reveal* · Prior predictive check on the calibration window alone
(1950–1990) showed the original prior put its **entire** mass below observed
primary energy: p95 of 237 EJ in 1990 against 320 EJ observed. The original
centre came from a back-of-envelope that took the 2020 capital stock from an
assumed capital–output ratio rather than from the model's own accumulation, and
was simply an arithmetic error. Recentred on zero — "no autonomous drift in
energy per unit of K–L composite" is the neutral null — rather than on the
data-preferred 0.0014, which would be fitting the centre rather than correcting
a mistake.

**Likelihood changed from independent-by-year to correlated discrepancy**
· *before reveal* · The first implementation scored each calendar year as an
independent observation. For a deterministic simulator this is not conservative,
it is wrong by about an order of magnitude in effective information: model–world
error is persistent, so nine points on a smooth 40-year series carry roughly
1.7 independent observations, not 9. Replaced with an exponential-kernel
covariance at 25-year correlation length (Kennedy & O'Hagan 2001).
Diagnosed from ESS = 1.0/3000 and PIT mass entirely in the tails.

**Sampler changed from prior importance sampling to tempered SMC**
· *before reveal* · Prior IS collapsed to a single particle (ESS 1.0 of 3000;
best draw beat second best by 13 nats) — unavoidable at 24 free parameters, and
not fixable by raising the draw count. The resulting "posterior predictive fan"
was one trajectory drawn 3000 times: a confident-looking empty result. Replaced
with adaptive tempered SMC. Post-change: 94% unique particles, acceptance
21–34%, 7 tempering stages.

Note that the correlated-likelihood fix, though correct and necessary, did *not*
resolve the collapse on its own — ESS stayed at 1.0. The two problems were
independent and both real.

### Post-reveal findings — recorded, not acted on

The 1990–2020 window was revealed after the posterior was frozen. Three
structural failures were identified. **None has been fixed**, because fixing
them now would be tuning against a revealed test set. They are logged here as
the agenda for M1/M2, where they must be re-frozen and re-scored from scratch.

**1. Land-use-change emissions are omitted, and it shows.**
CO₂ concentration runs 4.1–4.6% low with a near-constant bias, while emissions
run 17–30% *high*. That combination cannot come from a parameter being off; a
too-high emission flow into a too-low stock means carbon is entering the
atmosphere from a source the model does not have. The uptake coefficient
(0.55, i.e. airborne fraction 0.45) was calibrated against the Global Carbon
Project budget, which counts fossil **plus land-use** emissions — but the model
is fed fossil + cement only. Roughly 10–15% of the real source term is simply
absent. This was flagged in `SERIES_META` before the run, which is why it could
be identified rather than discovered.

*Note on timing:* the bias is visible at 1990, inside the calibration window,
so it was detectable without the test set. It was not detected before the
reveal. That is a process failure, not just a model failure — the pre-freeze
checklist should include a residual-sign check per series.

**2. Energy demand does not decouple.**
Primary energy tracks observation to +1.8% at 1990 and then diverges
monotonically to +24.7% by 2020. Demand is anchored to the K–L composite with a
constant exponential drift fitted on 1950–1990; the world after 1990 decoupled
(efficiency, shift to services, post-Soviet industrial collapse, China's
intensity programme). The model has no mechanism that can produce a regime
change in intensity.

This is design §2.2 — non-stationarity — appearing in the smallest possible
model on its first run. Parameters fitted on one regime failed on the next, and
the failure is exactly of the size the design predicted would matter.

**3. Emissions cannot plateau.**
Observed emissions flatten over 2015–2020 (35.5 → 35.0 GtCO₂). The model rises
monotonically. Carbon intensity declines at a fixed exponential rate, so a
plateau is not in its reachable set at any parameter value.

**4. The skill estimator itself is noisy, and a single-seed score is not a result.**
GDP skill came out at +5.7% with 1200 particles and −14.7% with 1500 — same
model, same data, same protocol, different Monte Carlo draw. Across five seeds
it ranges −93% to +7%. Six scored points is simply not enough to resolve a skill
difference of that size, and any single run's number is closer to a coin flip
than to a measurement.

Added `civsim stability` in response: it re-runs the whole protocol across seeds
and reports only verdicts whose sign survives. This is a change to *reporting*,
not to the model, and does not use the test window for fitting — it measures the
variance of an estimator that was already computed.

Five-seed result (1000 particles each):

| series | mean skill | range | verdict |
|---|---|---|---|
| population | +49.4% | +12.4% … +72.0% | **robust skill** |
| GDP | −38.5% | −93.2% … +7.3% | sign unstable — no demonstrated skill |
| primary energy | −43.2% | −97.2% … −2.9% | robust loss |
| CO₂ emissions | −54.6% | −131.8% … −19.6% | robust loss |
| CO₂ ppm | −451.8% | −477.8% … −403.7% | robust loss |

### What M0 predicted about itself, and what happened

Design §5 rated primary energy as likely to beat baselines and per-capita GDP
growth as unlikely to. **Both calls were wrong, in opposite directions.**

Energy was expected to win and robustly loses — because §5 reasoned about
whether energy demand is *predictable in principle* and did not ask whether this
particular model contains a mechanism capable of producing the observed
decoupling. It does not.

GDP was expected to lose and is instead indistinguishable from trend. That is
not a vindication: "indistinguishable from a trend extrapolation" is what §5
meant, and the initial positive number was noise.

Population's robust +49% is the one genuine win, and it is the one the design
called correctly and for the right reason: cohort inertia. M0 does not even have
cohorts — it has a saturating transition curve — and it still beats trend
extrapolation comfortably, which suggests §3.1 understated how much of the
predictability is structural rather than statistical.

The standing lesson for M1: a variable being predictable in principle says
nothing about whether the model in hand can predict it. Those are separate
claims and §5 conflated them.
