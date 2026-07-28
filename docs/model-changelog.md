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

---

## M2 — 2026-07-26

All three M1 follow-ups, in the order they had to be done: the discrepancy fix
first, because it is what makes adding an uncertain data series safe rather than
repeating M1's contamination.

### 1. Per-series discrepancy variance — estimated, not assigned

M1 asserted that the model is equally wrong about every channel. Measured, that
assertion was off by more than an order of magnitude:

| series | inferred discrepancy | M1 assumed |
|---|---|---|
| low-carbon share | 11–46% | 6% |
| CO₂ emissions | 6.3–9.6% | 6% |
| primary energy | 6.2–9.1% | 6% |
| GDP | 3.7–5.5% | 6% |
| population, CO₂ ppm, age shares | 2.3–4.3% | 6% |

Assigning a scale per series by hand would have fixed the symptom by fitting the
likelihood. Instead the scale is given an inverse-gamma prior and integrated out
analytically, turning each series' Gaussian into a multivariate Student-t. The
decisive change is that residuals enter through `log(b + Q/2)` rather than `Q`:
a badly modelled channel is charged a logarithmic penalty and reports itself as
badly modelled, instead of a quadratic one that overwhelms every other channel.
No sampled parameters are added.

**Result on M0's five series, four seeds, 1990 origin — only the likelihood
changed:**

| series | M0 | M1 | M2 |
|---|---|---|---|
| population | +49.4% | +12.6% | **+65.0%** robust |
| GDP | −38.5% | −38.7% | −63.0% |
| primary energy | −43.2% | −106.7% | −199.3% |
| CO₂ emissions | −54.6% | −34.1% | −88.9% |
| CO₂ ppm | −451.8% | −81.2% | −83.5% |

**Population's robust skill is restored and now exceeds M0's.** That was the
stated purpose and it worked.

The other channels got worse, and the reason matters more than the numbers. The
marginal-t likelihood no longer forces the calibration to chase a channel the
model cannot structurally fit, so it stops distorting shared parameters toward
energy — and energy's forecast falls to what the model is actually worth there.
**M1's −107% on energy was flattered**, bought by degrading population's fit.
M2 is not worse at energy; M2 stopped hiding how bad energy was.

### 2. Data that identifies the two energy channels

M1's energy regression was an identification failure: the service ladder and the
efficiency knowledge stock both multiply into primary energy, and aggregate
primary energy cannot separate them.

The observable that does separate them is conversion efficiency, which responds
to efficiency knowledge and not to the ladder. Added
`useful_exergy_efficiency_pct` — global primary-to-useful exergy efficiency from
the exergy-accounting literature — as a scored series.

It is **C-grade, deliberately**. Published estimates disagree on the level by
several percentage points while agreeing much better on the trend, so it
constrains the slope of conversion efficiency far more than its height. Adding a
series this uncertain is precisely what M1's uniform likelihood could not have
survived; its inferred discrepancy comes out at 3.0–4.9%, so it neither
dominates nor is ignored. Item 1 is what made item 2 safe, which is why it came
first.

Identification is improved, not solved. Full separation needs cross-section —
countries at different development levels sharing one technology frontier — and
that is M3, not more world-level time series.

### 3. Rolling origins, and a control for what they actually show

Four origins (1975, 1985, 1995, 2005), each running the full protocol
independently: own prior, own SMC, own freeze, own reveal. Scored points rise
from 6 to 28 per series.

The expanding-window result showed skill degrading as the origin moves later —
the §2.2 signature. But it is confounded: later origins have shorter test
windows, so the trend could be three noisy points rather than non-stationarity.

**Control run** (`civsim rolling --control`): every origin scored on the *same*
1995–2020 window, only the calibration end moving. This is asymmetric in the
useful direction — later origins have strictly **more** calibration data, so if
skill still degrades the "less data" explanation is gone too.

It still degrades: 6 of 9 series, mean −144 skill points per decade.

| series | pooled skill (18 pts) | 1975 | 1985 | 1995 | verdict |
|---|---|---|---|---|---|
| population | **+63.5%** | +74% | +43% | +74% | **robust skill** |
| useful exergy efficiency | +19.3% | +78% | −71% | −47% | sign unstable |
| working-age share | +8.5% | +82% | −135% | −499% | sign unstable |
| GDP | −20.6% | −35% | +57% | −41% | sign unstable |
| CO₂ ppm | −23.8% | +17% | −150% | −40% | sign unstable |
| CO₂ emissions | −38.9% | −84% | +70% | +10% | sign unstable |
| old-age share | −86.5% | −216% | −25% | +50% | sign unstable |
| primary energy | −138.1% | −120% | −81% | −1087% | robust loss |
| low-carbon share | −425.1% | −66% | −616% | −1281% | robust loss |

**Adding more recent calibration data makes forecasts worse.** That is the first
quantitative confirmation of design §2.2 in this project rather than an appeal
to it.

One honest alternative reading, which should travel with the finding: more
calibration data also tightens the posterior, and CRPS punishes a confident
wrong forecast harder than a vague one. So the mechanism may be less "the world
changed regime" and more "a structurally wrong model given more data becomes
more confident without becoming more accurate." Those are not the same claim.
The second is arguably the sharper and more useful one, and this experiment
cannot separate them.

### Standing scorecard

Robust skill on **1 of 9** series (population), across four origins and four
seeds. Everything else is a robust loss or sign-unstable. The `stability` and
`rolling` commands exist so that this cannot be reported any other way.

### For M3

1. **Cross-section.** The energy channels cannot be identified from world
   aggregates at all, and the low-carbon share's 11–46% discrepancy says the
   technology module is the worst-modelled part of the system. Both need
   countries at different development levels, which is the design's M3 anyway.
2. **The low-carbon share is the weakest channel by a wide margin** and should
   be attacked before anything else in the technology layer is elaborated.
3. **Correlated errors *between* series.** The likelihood still treats series as
   independent given their scales. They are not — if energy runs high, emissions
   run high — and that correlation is currently double-counting evidence.

---

## M3 — 2026-07-26

All three M2 follow-ups, again in dependency order: the likelihood fix first,
because regionalisation doubles the series count and the same-name series across
regions are the most correlated pair in the system.

### 1. Cross-series error correlation

M2 gave each series its own discrepancy scale but kept them conditionally
independent. They are not: emissions are computed *from* energy in this model, so
a particle running energy 20% high runs emissions high by construction. Scoring
both as independent evidence counts one error twice, and with nine series mostly
strung along one causal chain the joint likelihood was far sharper than the
information warranted.

The fix is the matrix generalisation of M2's. Residuals stack into a p×n matrix
(series by year), modelled matrix-normal with separable covariance Σ ⊗ C, with
an inverse-Wishart prior on Σ integrated out analytically. The result is a
matrix-t whose decisive term is `log|Ψ + R C⁻¹ R'|` — a **determinant** where M2
had a sum of per-series scalars. Aligned residuals make that matrix nearly
singular in their shared direction, so the determinant barely grows and the
evidence is not double-counted. Orthogonal residuals grow it fully, which is
correct. No sampled parameters added.

Measured error correlations, which are the diagnostic that was missing:

| pair | correlation |
|---|---|
| energy ↔ emissions | **+0.92** |
| emissions ↔ GDP | +0.73 |
| energy ↔ GDP | +0.66 |
| low-carbon share ↔ exergy efficiency | −0.55 |

Likelihood discrimination across particles fell from 105 to 89 nats — the
correct direction, since the extra sharpness was an artefact.

### 2. The low-carbon channel: two technology families

Observed world low-carbon share rises, sits on a twenty-year **plateau**
(11.3% in 1990 → 12.6% in 2010), then resumes. One technology family with one
learning rate and one ceiling cannot produce that at any parameter value — the
same structural impossibility as M0's inability to plateau emissions, and why
this was the model's worst channel (11–46% inferred discrepancy).

Split into dispatchable (hydro, nuclear: slow learning, hard resource-and-social
ceiling) and modular (wind, solar: steep learning, a base small enough to be
invisible for decades). The plateau then emerges as the gap between one
saturating and the other arriving. Prior draws producing rise → pause → faster
resumption went from 0% to 4%; the shape is now in the reachable set.

Cost: five parameters, plus a softened adoption logistic. M2's sharpness of 6
made the transition a threshold rather than a gradient — a technology at 1.9×
parity got a 0.5% share, which the historical record contradicts.

Inferred discrepancy on the channel improved from 11–46% to 21.5%. Still the
worst channel by a factor of two.

### 3. Cross-section: two regions

Two regions, `hi_` (high income) and `lo_`. **Almost every parameter stays
global** — the energy service ladder and the demographic transition are single
functions of development that both regions sit on at different points, since
their capital per head differs by roughly a factor of five. The cross-section
therefore adds identifying information without enlarging the parameter budget.
Only the saving rate is regional.

Regional levels are world totals times an observed share, so the regions sum to
the world by identity and the C-grade uncertainty is confined to the split.

A deliberately falsifiable prediction: technology is global, so `hi_co2_share`
must equal `hi_energy_share` exactly. Observation says 38% of energy but 33% of
CO₂ in 2020. It is scored anyway and fails (−200% robust loss). The gap measures
how much regional technology heterogeneity matters, which is worth more than
omitting a prediction the model is committed to.

### The structural failure this exposed, and the trade-off it forced

The first two-region build had the **lagging region's capital per head overtake
the leader's** by 2020 (ratio 4.41 → 0.88). A shared global frontier plus Solow
accumulation drives full convergence and then overshoot. Poor regions overtaking
rich ones is not a subtle calibration error, and it was visible inside the
calibration window (ratio already 1.26 by 1990).

Fixed with absorptive capacity (design §8, L3; Nelson-Phelps): a region captures
the frontier only to the extent its own development lets it. Overshoot
eliminated — 0 of 38 draws now cross over, median ratio 3.74.

**And it made the backtest worse across the board:**

| | without absorption | with absorption |
|---|---|---|
| robust skill | 2/13 | **1/13** |
| hi_gdp_share | **+40.6%** robust skill | −73.7% robust loss |
| population | +44.1% | +33.7% |

The diagnosis is uncomfortable and worth stating plainly: the no-absorption
version fitted the observed 1950–2020 convergence of the income split **by
over-converging**, and paid for it with an absurd extrapolation just past the
scored window. The parameters that reproduce historical catch-up imply overshoot
afterwards. The model can do one or the other, not both.

**The absorption version ships.** Same reasoning as M1's technology layer:
backtest skill over 1950–2020 cannot see an overshoot that begins in 2020, and a
model in which poor regions overtake rich ones is unusable for every forward
question this project exists to ask. The score is the honest cost.

A likely part of the residual: the high-income group has fixed membership in this
data, while in reality countries graduated into it. Some of the observed share
decline is compositional and no dynamic mechanism can or should reproduce it.
That was flagged in the series metadata before the run, not after.

### Standing scorecard

Robust skill on **1 of 13** series (population, +33.7%). Everything else is a
robust loss or sign-unstable.

Four milestones in, the model has robust skill on exactly one variable, and it
is the one design §3.1 predicted for the reason §3.1 gave — cohort inertia.
Every added mechanism has been structurally necessary and has cost backtest
skill. That is now a pattern rather than an accident, and the design's §15.1
merge rule has been overridden three times on the same argument: reachable-set
coherence is not measurable by hold-out skill. If that argument is wrong, the
last three milestones were a mistake.

### For M4

1. **Time-varying region membership**, or accept that part of the convergence
   signal is compositional and stop scoring against it.
2. **Regional technology deployment** — the one prediction the model was
   committed to and failed by construction.
3. **Regional age structure at t0.** Both regions currently start from the world
   age distribution, which is badly wrong for 1950 and is the most likely cause
   of the working-age share being the worst channel (−648%).

---

## M4 — 2026-07-26

M4 changes direction. The first four milestones all added mechanism and all cost
backtest skill; the pattern is now four data points deep and continuing it would
be self-justification rather than development.

The more likely reading is already in the design. §1.5's per-variable
feasibility table predicted this outcome: population predictable, GDP growth
"几乎不能", the rest in between. Four rounds of increasingly careful mechanism
have confirmed that table empirically. **That is a result, not a failure** — and
it means chasing skill is the wrong objective.

Design §7 says the product is four things: probability fans, **the set of paths
ruled out by constraint**, **bifurcation and sensitivity maps**, and an audit
trail. Two of them had never been built, and the model had never been run
forward even once. M4 builds them.

The point of those two outputs is that **neither requires predictive skill.**
A model with skill on 1 of 13 series cannot say what 2100 looks like. It can
still say which futures are unreachable without violating conservation, and
which parameters the spread actually turns on.

### A kernel conflation the exclusion analysis exposed

Sweeping 120 prior draws to 2100, 33 hit a floor on an accounting reservoir and
13 hit the fossil carbon reserve. Reported together those look like one finding
about the world. They are opposites: the second is a physical limit, the first
was an arbitrary 1e7 pool I had sized by guess, and three quarters of the
"finding" would have been a statement about my own constant.

`Limit.PHYSICAL` vs `Limit.RESERVOIR` now separates them at the type level.
Exhausting a physical limit raises `ConstraintBinding` and is counted as data.
Exhausting a reservoir raises `ReservoirUndersized`, is never caught, and is
labelled a bug in its own message. A test asserts no reservoir binds in a full
forward run, because if one ever does the exclusion counts are contaminated.

### What the exclusion analysis actually found

**Nothing is excluded.** 700/700 posterior draws reach 2100 with no physical
limit binding. Reported plainly because it is the honest result, and because it
is more informative than it first looks:

- Over the *prior*, fossil carbon reserves bind in ~11% of draws (median 2055).
  Over the *posterior*, never. Calibration on 1950–2020 concentrates the
  parameters in a region where depletion does not bite this century.
- So in this model **the binding constraint on emissions is the low-carbon
  transition, not running out of fossil carbon.** That is a genuine and
  non-obvious statement of the kind §7 promised, and it does not depend on any
  forecast being right.

Target reachability, with excluded draws in the denominator:

| target at 2100 | reachable |
|---|---|
| CO₂ ≤ 450 ppm | **0.0%** |
| CO₂ ≤ 550 ppm | 37.6% |
| primary energy ≥ 1000 EJ | 73.4% |
| low-carbon share ≥ 50% | 98.9% |
| population ≤ 10 bn | 87.6% |

### Sensitivity: what the spread actually turns on

Standardised regression, not Sobol — linear-additive and it will understate the
interactions the technology module is full of. Used because it costs one
existing ensemble instead of a dedicated sample of tens of thousands, and
because "which knobs matter at all" survives the approximation. Anything that
looks decisive here needs a proper Sobol index before it is believed.

| outcome at 2100 | top drivers |
|---|---|
| population | `fert_half` +2.06, `depreciation_rate` +1.06 |
| GDP | `tfp_elasticity` +0.84, `fert_half` +0.77 |
| primary energy | `energy_service_theta` +0.77, `fert_half` +0.62 |
| CO₂ ppm | `energy_service_theta` +0.78, `learning_rate_modular` −0.54 |

The result worth flagging: the largest single lever on 2100 concentration is the
**shape of the energy service ladder**, not the learning rate — demand-side
saturation ahead of supply-side learning. That is not what the technology
literature would lead you to expect, and it is exactly the sort of claim that
should be checked with a real Sobol decomposition before anyone acts on it.

Note also that `fert_half` appears in three of the four rows. Demography is the
model's dominant uncertainty even for energy and carbon outcomes — consistent
with it being the one channel with robust skill, and a caution that the others
inherit their spread from it.

### Path archetypes

k-means on standardised log-trajectories concatenated across population, GDP,
energy and concentration, so an archetype is a whole-system story rather than
one variable's shape. Four clusters, sizes 248/191/145/116. A summarisation
device, not an inference.

### Standing position

Robust backtest skill: **1 of 13** series. Unchanged, and not the objective any
more. The forward chart states that verdict on every panel, so a projection of a
channel that loses to trend extrapolation cannot be read as a forecast without
also reading the caveat.

### For M5

1. **Proper Sobol indices** for the drivers above. The service-ladder result is
   too surprising to rest on a linear approximation.
2. **Scenario inversion** — instead of sweeping parameters and seeing what comes
   out, ask what would have to be true for a stated target and test whether that
   combination is internally consistent. That is the question policy actually
   asks, and the constraint machinery is now in place to answer it.
3. The exclusion analysis found nothing because the posterior is narrow. It
   becomes informative when the model is asked about futures further from the
   calibrated region — which is what (2) does.
