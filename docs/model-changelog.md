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

---

## M1 — 2026-07-26

Adds the L3 technology layer the design specified and M0 omitted, an
age-structured population, and the land-use emissions M0's residuals pointed at.

### The honest headline

**M1 has robust skill on zero series. M0 had one.** Measured across four seeds
on M0's own five series, so the comparison is like-for-like:

| series | M0 mean | M1 mean [min, max] | verdict |
|---|---|---|---|
| population | **+49.4%** | +12.6% [−57, +63] | robust skill lost, now unstable |
| GDP | −38.5% | −38.7% [−79, −15] | robust loss, unchanged |
| primary energy | −43.2% | **−106.7%** [−182, −19] | robust loss, materially worse |
| CO₂ emissions | −54.6% | −34.1% [−74, +15] | improved, sign unstable |
| CO₂ concentration | −451.8% | **−81.2%** [−191, +36] | hugely improved, still a net loss |

Two things went right and two went wrong, and they are separable.

**Right: the land-use fix worked, exactly as diagnosed.** Concentration was
M0's worst failure by a factor of eight. Adding the missing source term moved it
from −452% to −81% mean, with individual seeds reaching +52%. The M0 residual
diagnosis — too-high emissions with too-low concentration means a missing
source, not a wrong parameter — was correct and led straight to the fix.

Caveat that must travel with that number: the improvement is partly from
compensating errors. In the frozen run, concentration tracked to 0.5% MAPE while
fossil emissions ran 23% high. The calibration achieved a good concentration by
choosing a high uptake coefficient that offsets an emissions path that is too
steep. The carbon module is *less wrong*, not right.

**Wrong: the technology module made energy substantially worse** (−43% → −107%,
robust across every seed). Energy demand now has two opposing mechanisms — a
service-demand ladder rising with development, and efficiency knowledge pushing
the other way — where M0 had one exponential. Aggregate primary energy cannot
separate them. Any (ladder, efficiency) pair that reproduces 1950–1990 is
admitted, and they diverge afterwards. Adding a mechanism that is not separately
observable made the forecast worse, which is §2.1 in its purest form: the fix is
not a better prior but data that identifies the channels separately, which means
sectoral intensity series and belongs to M2.

**Wrong: the age-structured population lost M0's one robust win** (+49% → +13%,
sign unstable). Three Erlang-staged compartments are more realistic than one
aggregate stock and forecast worse. The working-age and old-age shares the model
now has to fit are themselves fitted badly (5.3% and 21.3% MAPE), and their
misfit drags the shared development-response parameters away from where
aggregate population alone would have put them.

### By the design's own merge rule, the technology module fails

§15.1 states: *every new subsystem must demonstrate that it improved the
hold-out score before it may be merged.* On backtest evidence the technology
module does not, and neither does the age structure.

**They are retained anyway, and the reason needs to be on the record rather than
assumed.** M0's diagnosis was that an emissions plateau lay outside its
reachable set *at every parameter value*, and that no decoupling could occur.
Those are statements about which futures the model can represent, and backtest
skill over 1950–2020 cannot measure them: a model can track history well while
being structurally incapable of the transition every forward scenario turns on.
The technology layer changes the reachable set. That is what a scenario
generator needs and what §15.1 was not written to weigh.

The consequence is that **the technology module is currently unfalsified, not
validated.** It has not earned a claim to be right. It has earned a claim to be
necessary. Those must not be conflated in anything this model is used for.

### Two defects found and fixed during M1

**Diffusion deadlock (found post-reveal, structural).** The first M1 build could
not represent any energy transition. Learning needs deployment, deployment needs
cost parity, cost parity needs learning; the target share sat at 1/(1+e¹⁸) and
the low-carbon share fell from 2.5% to 0.03% over seventy years while retirement
ate capacity that was never replaced. **Every conservation check passed
throughout.** Fixed by adding a niche deployment floor — hydro plus the policy
demand that historically bought nuclear and solar learning above market price —
which is the standard niche-to-regime mechanism, not a numerical patch.

Diagnosable from calibration data alone (the collapse is visible by 1990), so
this was a process failure as well: nothing in the pre-freeze checklist looked at
the technology module's own output. Fixed by adding `lowcarbon_share_pct` as a
scored series, so the technology layer is now falsifiable on its own terms
instead of only through emissions.

**Negative conversion efficiency (found pre-reveal, robustness).** When
knowledge fell below its t0 index, `eff = eff_inf − (eff_inf − eff_0)·exp(−r·(A−1))`
flipped sign, useful work went negative, and the CES bracket returned a *complex
number* that propagated silently until something compared it to zero.

The lesson is general and now has a test: **conservation is necessary and not
sufficient.** Nothing was created or destroyed, so the ledger saw nothing wrong.
Quantities with physical ranges — a fraction, a share, a probability — need
their ranges asserted separately from their balances.

### Deliberately not done

Single-year cohorts. They need age-specific fertility and mortality schedules,
roughly forty parameters against nine 5-yearly aggregate observations. The M1
result above is what happens when mechanism is added faster than the data can
identify it; doing it again deliberately would not be a mistake, it would be a
decision to produce noise.

### For M2

1. **Per-series discrepancy variance.** The likelihood currently assigns every
   series the same 6% structural scale. A series the model fits at 27% MAPE then
   dominates the joint likelihood and contaminates parameters shared with series
   it could fit well. This is the most likely single cause of the population
   regression and should be estimated, not assigned.
2. **Sectoral energy intensity data**, without which the ladder and efficiency
   channels stay unidentified.
3. **Rolling-origin scoring.** Six scored points cannot resolve skill; multiple
   cutoffs would both raise the point count and test the non-stationarity claim
   directly.
