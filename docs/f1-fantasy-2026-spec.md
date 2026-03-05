# 2026 F1 Fantasy Winning Strategy and WebApp Spec for Decision Support

## Rules and scoring model for the 2026 game

### Fundamentals you must model exactly

The 2026 official game is a season-long salary-cap fantasy format where you pick **five drivers + two constructors** inside a **$100m starting cost cap**, and you can run **up to three teams** under one account. citeturn22view0turn21view0

Once the season is under way, you get **two free transfers per Grand Prix round per team** (with penalties for exceeding the allowance). citeturn22view0

A key 2026 usability change is **Net Transfers**: transfers “count based on final changes, not every tap,” meaning you can swap out and swap back before the deadline without automatically consuming multiple transfers. This matters for both UX and optimization (you should treat intermediate edits as “draft states,” and only compute transfers on the final submitted team). citeturn22view0

Sprint weekends exist in 2026 and materially change planning because they add an extra scoring session. Formula 1’s announced **six Sprint weekends** are: **China, Miami, Canada, Great Britain, Netherlands, Singapore**. citeturn23search0

Your product should ingest the full 2026 season calendar (round numbers, dates, locations) directly from the official race calendar page to drive automation (lock timers, sprint detection, scheduling jobs, “chip candidate” suggestions). citeturn23search16turn23search0

### Scoring system (drivers and constructors)

Below is a **2026-accurate scoring model** distilled from the official game rules page. The app should store these in a **versioned ruleset table** (see schema section) so you can replay historical weeks if rules change midseason. citeturn24search1turn29search0turn30search1turn27search0turn28search0

**Qualifying (Drivers)**  
Qualifying finishing position points: **P1=10 … P10=1, P11–P20=0**; **NC/DSQ/No time set = -5**. citeturn24search1turn18search0

**Qualifying (Constructors)**  
Constructor qualifying points include: (a) sum of both drivers’ qualifying points, and (b) “qualifying progression” bonuses: **neither reaches Q2 = -1; one reaches Q2 = 1; both reach Q2 = 3; one reaches Q3 = 5; both reach Q3 = 10**. citeturn17search0turn18search0  
If a driver is disqualified in qualifying, rules text indicates a **-5 per disqualified driver** treatment in the qualifying context (model this explicitly so the scoring audit trail is interpretable). citeturn17search0

**Sprint (Drivers)**  
Sprint finishing points: **P1=8 … P8=1, P9–P20=0**. citeturn29search0turn30search1  
Sprint bonuses/adjustments include: **positions gained +1 per position; positions lost -1 per position; overtakes +1 per overtake; fastest lap +10; Driver of the Day +10**. citeturn28search0  
Sprint “not classified” outcomes: rules specify **No time set = -10** and **Disqualification = -10** in Sprint scoring. citeturn15search0turn29search0  
A 2026 headline change is that Sprint retirements/NC penalties “sting less” because the Sprint DNF penalty is now **-10**. citeturn22view0turn15search0

**Sprint (Constructors)**  
Constructors score the combined Sprint points of their two drivers (i.e., sum of each driver’s Sprint score components that are constructor-eligible). citeturn17search0turn29search0

**Race (Drivers)**  
Race finishing points mirror official F1 race points: **P1=25, P2=18, P3=15, P4=12, P5=10, P6=8, P7=6, P8=4, P9=2, P10=1, P11–P20=0**. citeturn30search1  
Race bonuses/adjustments: **positions gained +1 per position; positions lost -1 per position; overtakes +1 per overtake; fastest lap +10; Driver of the Day +10 (driver-only)**. citeturn16search0turn28search0  
Race “not classified” outcomes: rules specify **DNF/no time set = -20** and **Disqualification = -20** in Race scoring. citeturn29search3turn30search1

**Race (Constructors)**  
Constructors score the combined Race points of their two drivers **excluding the Driver of the Day bonus**. citeturn13search1turn29search3  
Constructors also score **pit stop points** based on the team’s **fastest pit stop time** in the race:
- **2.20–2.49s = 5 points; 2.00–2.19s = 10 points; under 2.0s = 20 points**, plus the rest of the banding implied on the rules page. citeturn27search0  
- **Fastest pit stop of the race = +5 bonus**  
- **New world record = +15 bonus** citeturn27search0turn27search5  
- **Disqualification = -20 per disqualified driver (constructor-side)** citeturn27search0turn29search3

### Chips and constraints (2026 definitions + unlock rules)

The 2026 season includes **six chips**, each **usable once per season**, and **only one chip can be used per race week**. citeturn21view0turn21view1

Official strategist definitions (treat these as canonical for in-app copy and rules logic): citeturn21view0turn21view2

- **Limitless**: for one race week, **unlimited transfers** and you **ignore the budget cap**; your team “returns to normal” the following week; **can only use from Round 2**. citeturn21view0  
- **Wildcard**: **unlimited transfers** while staying within your **current cost cap**; **can only use from Round 2**. citeturn21view0  
- **3x Boost**: one driver scores **triple points**, while a second driver can score **double points** via the regular 2x boost. citeturn21view0  
- **No Negative**: any points your team would lose are set to **zero** for that race week (examples cited: DNFs, positions lost). citeturn21view0turn20search0  
- **Final Fix**: after the deadline has passed, you can **replace one driver** before the race start. citeturn21view0  
- **Autopilot**: the game automatically applies the **2x boost** to your highest scoring driver for the week. citeturn21view0turn25search0

Secondary explainer content (useful for UI education and “pitfalls” callouts, but do not treat as authoritative when it conflicts with official): the chip ecosystem historically includes Autopilot, Extra DRS Boost naming variants, No Negative, Wildcard, Limitless, Final Fix. citeturn10search19

### Rules glossary (rule → data needed → computation)

Implement this as a **rules engine** backed by a versioned ruleset + an auditable points ledger. Representative mapping:

| Rule / mechanic | Data you must store | How the app computes it |
|---|---|---|
| Cost cap, roster size | asset prices by round; roster snapshot | Validate 5 drivers + 2 constructors under cap at lock; compute remaining cap and total value citeturn22view0turn21view0 |
| Transfers + Net Transfers | submitted team at lock; prior round team; “draft edits” | Compare last saved team to final submitted team to count transfers (ignore intermediate edits), then apply penalty if transfers beyond free allowance citeturn22view0 |
| Qualifying / Sprint / Race scoring | official session classification; lap/overtake events; DOTD | Transform session results/events into points using rules tables; write to points ledger with category tags citeturn24search1turn29search0turn30search1turn28search0 |
| Overtakes definition | overtake events list | Count only “legal on-track pass” events (exclude pit-lane / abnormal slow / failures per rules text); store provenance and event IDs citeturn29search3 |
| Pit stop scoring | pit stop times per constructor | Compute constructor’s fastest pit stop time; map to buckets; add +5 fastest overall and +15 record rules citeturn27search0turn27search5 |
| Chip eligibility + effects | chip inventory; chip usage history; lock timestamps | Enforce “once per season” and “one per week”; apply chip transforms to scoring or team state as specified (Limitless/Wildcard team building, 3x/2x multipliers, No Negative floor, Final Fix post-lock swap, Autopilot auto-boost) citeturn21view0turn21view1 |
| Sprint weekends | official sprint calendar (rounds) | Tag rounds as sprint/non-sprint; adjust UI defaults, simulation, and chip EV computations accordingly citeturn23search0turn23search16 |

## Winning definition and optimization framework

### What “winning your league” means in practice

The product should support at least three “win conditions,” because the optimal risk posture differs:

**Season total points maximizing** (classic private league): maximize expected season points subject to transfer and chip constraints. citeturn22view0turn21view0

**Head-to-head / matchup formats**: Formula 1 explicitly mentions head-to-head league play; for those leagues, you often want to maximize the probability of beating a specific opponent in a given round, not purely season EV. citeturn22view0

**Tournament-style global rank chasing**: if you’re trying to win very large leaderboards, higher variance (more upside) strategies can dominate. (This is an inference; the app should let the user choose a risk profile and show tradeoffs.)

### Formal problem statement

Model each race week \(t \in \{1,\dots,T\}\) as a stochastic outcome distribution over:

- driver outcomes: grid position, finish position, overtakes, fastest lap, DOTD, not-classified events, DSQ  
- constructor outcomes: both drivers’ outcomes + pit stop bucket and bonuses citeturn30search1turn27search0turn28search0

Let decision variables at each week \(t\):

- \(x_{t}\): binary vector representing selected assets (5 drivers, 2 constructors)  
- \(b_{t}\): which driver gets the standard 2x boost  
- \(c_{t}\): which chip is used (or none) subject to “one/week” and “once/season” constraints citeturn21view0turn21view1  
- \(u_{t}\): transfers applied (net transfers constraint) citeturn22view0  

State variables:

- remaining chip set \(C_t\)  
- current cost cap / total value and live asset prices  
- transfer bank/allowance representation (at minimum: free transfers each round, plus penalty per extra transfer) citeturn22view0turn29search3

Objective options (implement all as “optimizer modes”):

- **Max EV**: maximize \(\mathbb{E}[\sum_t P_t]\)  
- **Mean–variance**: maximize \(\mathbb{E}[\sum_t P_t] - \lambda \cdot \mathrm{Var}(\sum_t P_t)\)  
- **CVaR**: maximize expected points subject to a constraint on downside tail \(\mathrm{CVaR}_\alpha\)  
- **Win probability vs league**: maximize \(\Pr(\sum_t P_t > \sum_t P^{(opp)}_t)\) using opponent forecast distributions (requires importing league rosters and estimating their behavior)

This is a constrained stochastic control problem. In production, you’ll solve it with a hybrid approach:

- **myopic weekly optimizer** (fast, good enough for most users)  
- **lookahead planner** (limited-horizon dynamic programming / Monte Carlo tree search over a small set of candidate transfer/chip actions)  
- **scenario library** (precomputed “chip weeks” + “constructor core” options) to keep compute bounded

## Predictive modeling and simulation engine specification

### Data sources you should treat as primary for race-weekend telemetry and timing-derived features

**OpenF1** provides a unified API with real-time and historical session data; for modeling and ingestion, you’ll lean especially on:
- **/sessions** (session metadata) citeturn32view1  
- **/laps** (lap-by-lap timing + sectors) citeturn32view2  
- **/weather** (track weather, updated every minute) citeturn32view0  
- **/race_control** (flags, safety car, incidents) citeturn32view3  

OpenF1’s public docs also make clear it offers both historical and live telemetry, and that access/support can vary by plan (your app should be robust to missing real-time access by using delayed ingestion). citeturn13search24turn2view2

**FastF1** is a Python library for accessing official timing data and telemetry (useful for deeper feature engineering like stint pace, lap-time distributions by tyre life, and teammate deltas). citeturn2view3

### Simulator outputs (minimum required)

For each upcoming round \(t\), your backend must output, per driver and constructor:

- expected fantasy points distribution: mean, median, p10/p90, probability of negative week, probability of “boom” outcomes (define as p90 threshold)  
- probability of “not classified” outcomes and DSQ-like events (in practice: any outcome that triggers the rules’ negative buckets) citeturn29search3turn30search1  
- probabilities of top-k finishes and key thresholds that drive fantasy scoring (e.g., finishing points zones, qualifying top-10, Q3 reach via proxy) citeturn30search1turn17search0  
- scenario splits: dry vs wet; high vs low safety car likelihood proxies (from race_control history); “overtake-rich” vs “track-position” weekends

For each candidate lineup under constraints:

- projected points distribution  
- marginal contribution by asset (Shapley-like attribution optional for later)  
- “price change expectation” proxy (see value model approach below)

### Layered modeling approach (implementation-ready)

**Base performance model (pace + finishing distributions)**  
Recommended structure:

1) **Session-anchored pace prior**  
Use last N events + same-circuit history to estimate baseline pace by constructor and driver. With 2026’s new technical era, weight **current-season data** heavily once available; early season should use broader priors (team strength tiers, testing signals, and uncertainty inflation—a modeling choice). citeturn21view0

2) **Practice/quali update**  
As sessions occur, update pace with:
- practice long-run pace estimate (e.g., median of representative stints)  
- quali single-lap pace estimate from best laps  
These can be engineered from OpenF1 laps and FastF1 timing/telemetry. citeturn32view2turn2view3

3) **Overtake and position-change model**  
Fantasy scoring explicitly rewards overtakes and positions gained/lost. citeturn28search0turn29search3  
Model position changes as a function of:
- starting position uncertainty (pre-quali) and grid position (post-quali)  
- race pace differential distributions  
- track “passability” latent factor learned from historical overtake rates and DRS/safety car dynamics (derived from race control + lap-by-lap position APIs)

**Reliability / “not classified” hazard model**  
Because the scoring penalties for not-classifying events are large (e.g., -20 in the Grand Prix), you need a first-class reliability model. citeturn29search3turn30search1  
Implement as:

- **cause-agnostic hazard** per driver/constructor: \(h(t)\) conditioned on team, driver, circuit, and weather  
- covariates: historical mechanical DNFs, incident DNFs, safety car frequency, lap-1 incident propensity proxy, and “new regulation era” volatility inflation early season (modeling choice)

OpenF1 race_control provides flags/safety car and incident messages you can use as inputs and for backtesting incident likelihood. citeturn32view3

**Weather impact model**  
Weather affects:
- variance of lap times and finishing order  
- incident rates (spin/crash likelihood)  
- overtakes/position changes (depending on conditions)

OpenF1 weather is updated every minute and includes air/track temperature, wind, humidity, rainfall. citeturn32view0  
Implementation approach:

- learn distributions of “pace delta” and “variance multiplier” conditioned on weather features  
- implement mixture scenarios: {dry, mixed, wet} with weights from (a) forecast API and (b) OpenF1 observed session weather once live sessions begin

### Monte Carlo engine spec (10,000+ sims per round, configurable)

**Core loop per simulation draw**:

1) Sample scenario variables:
- weather regime (dry/mixed/wet)  
- safety car regime (none / VSC-like / SC / red-flag proxy) using race_control history priors citeturn32view3  
- grid positions if pre-quali (sample from quali model); otherwise use actual quali order

2) Sample per-driver latent performance:
- pace offset  
- error/aggression factor (impacts overtakes + incident hazard)  
- reliability hazard event time

3) Simulate race order and events:
- convert pace to finishing distribution (e.g., Plackett–Luce with noise or Gaussian copula on finishing positions)  
- generate overtakes and positions gained/lost consistent with start/finish positions and track passability constraints  
- generate fastest lap / DOTD proxies (DOTD is user-voted; treat as probabilistic feature driven by “hero drive” narratives—keep separate and low-weighted unless you have a robust model). DOTD is explicitly worth +10. citeturn28search0turn7search18

4) Apply fantasy scoring transform:
- compute points for qualifying/sprint/race according to session type and official scoring tables  
- apply chip transforms (3x/2x, No Negative floors, Autopilot selection) citeturn21view0turn21view1

5) Aggregate:
- store per-asset and per-lineup summaries (mean, p10/p50/p90, tail risk metrics)  
- store “decision table” outputs for UI ranking

**Output artifacts your app should persist**
- per asset: distribution summaries + scenario-conditioned summaries  
- per lineup: distribution summaries + component breakdown (qualifying vs sprint vs race; overtakes/positions vs finish points; pit stop points contribution for constructors) citeturn27search0turn28search0  
- per simulation run: full metadata (ruleset version, model version, data cut timestamp, assumptions, seeds)

## Decision support features: team builder, strategies, chip planner, and weekend checklist

### UX inspiration target

A strong benchmark is the “toolbox” model: separate pages for a team calculator, budget builder, live scoring, and post-hoc analysis features. The referenced site lists **Team Calculator**, **Budget Builder**, **Live Scoring**, and deeper analysis tools (some premium). citeturn10search18

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["F1 Fantasy Tools team calculator screenshot","F1 Fantasy Tools budget builder screenshot","F1 Fantasy Tools live scoring screenshot"],"num_per_query":1}

### Strategy playbooks (five complete approaches)

Each playbook should be shipped in-app as a “mode” that sets optimizer objective + risk constraints + chip preferences.

**Value-growth first (early cap building, later premium stacking)**  
Philosophy: early season focus on assets whose expected points-per-dollar and likely value appreciation are high, accepting some week-to-week variance; later season converts built cap into “premium cores.” This aligns with official emphasis on early budget growth and “value picks.” citeturn21view0turn22view0  
Decision rules:
- early rounds: prefer constructors with stable pit stop points + decent finishes, because pit stop scoring can create large, repeatable weekly edges citeturn27search0turn27search5  
- use Wildcard soon after the game reveals true team pace tiers (Round ≥2 constraint) to rebase into the best “value frontier” citeturn21view0  
Failure modes:
- if early-season DNFs spike, value chasing can backfire; mitigate with No Negative on the highest-risk week once you have a clear risk signal citeturn21view0turn19search17  
App signals:
- “value delta” dashboard: projected points-per-million, projected volatility, and expected cap change proxies.

**Constructor core lock (set-and-forget teams, rotate drivers)**  
Philosophy: pit stop points + two-driver aggregation means constructors can contribute a large share of weekly points; keep two “core constructors” and rotate driver slots for form and track fit. Constructors explicitly score combined driver race points plus pit stop points. citeturn13search1turn27search0  
Decision rules:
- only transfer constructors when expected weekly delta (including pit stop bucket and DSQ exposure) exceeds a threshold (e.g., >8–12 expected points) or when a structural shift is detected (upgrades, reliability)  
Failure modes:
- locking constructors too early in a new regs year can be wrong if the competitive order reshuffles; mitigate by postponing “lock” until after you have multiple rounds of pace evidence citeturn21view0turn22view0  
App signals:
- constructor stability index: rolling median points + pit stop bucket frequency + reliability hazard.

**High-variance chaos hunting (maximize probability of spike weeks)**  
Philosophy: in leagues where you need to catch up, maximize upside and tail outcomes: wet races, high-incident tracks, midfield overtake monsters, and Sprint weekends. Sprint weekends offer an extra scoring session. citeturn23search0turn26search13  
Decision rules:
- choose drivers with high overtake and position-gain potential because those categories award points directly citeturn28search0turn29search3  
- prefer Sprint weekends for 3x Boost because you have “an additional session of point-scoring opportunities.” citeturn26search15turn23search0  
Failure modes:
- increased DNF/NC risk can destroy weeks; mitigate with No Negative on the single highest predicted-risk week citeturn19search17turn21view0  
App signals:
- “chaos index”: weather variance, safety car probability proxy, start-line incident priors.

**Sprint-weekend exploitation (structural edge)**  
Philosophy: target weeks where the rules create more scoring surface area (Sprint + GP), then concentrate multipliers and Limitless. Sprint weekends and their venues are officially listed for 2026. citeturn23search0turn23search16  
Decision rules:
- allocate at least one of: Limitless, 3x Boost to Sprint weekends unless the season dominance pattern makes a non-sprint “guaranteed sweep” week higher EV (rare) citeturn21view0turn26search15  
- plan around lock logic and avoid last-minute scrambling by using calendar-driven alerts and “what-if” drafts (especially with net transfers) citeturn22view0turn23search0  
Failure modes:
- Sprint lock deadlines compress decision time; mitigate with automated “Friday model run” and “pre-lock safe lineup” presets.

**Opponent-aware blocking (private league game theory)**  
Philosophy: in a small private league, your job is often to beat 5–15 specific opponents, not the global field. The app should:
- ingest opponent rosters (manual entry or league scrape if available)  
- model their likely transfers (behavioral model)  
- recommend either (a) **block picks** (match their high-confidence assets) or (b) **leverage picks** (differentials + chip timing) depending on your season position.

Decision rules:
- if you’re ahead: reduce variance; match their highest-confidence constructor(s), then use safer driver portfolio  
- if you’re behind: increase variance by concentrating chips on weeks where opponents are unlikely to match, and pick differentials with high p90 but acceptable downside  
Failure modes:
- overfitting to opponent guesses; mitigate with robust “opponent range” modeling and show confidence bands.

### Team calculator specification (modes + constraints)

**Core UI**  
A “Team Builder” page with:
- roster slots (5 drivers, 2 constructors) + budget bar and remaining cap citeturn22view0  
- transfer counter (free vs penalized) using net-transfer semantics citeturn22view0  
- chip selector with eligibility and once-per-season enforcement citeturn21view0turn21view1  
- per-asset point distributions + breakdown by session (Quali/Sprint/Race) tied to official scoring categories citeturn30search1turn29search0turn28search0  

**Required optimization modes** (backend service must support all as first-class endpoints)
- **Max EV**: maximize expected points this week  
- **Max upside**: maximize p90 (or expected points subject to a minimum variance)  
- **Min downside**: maximize p10 (or maximize EV subject to CVaR constraint)  
- **Value growth optimizer**: maximize expected *future* purchasing power (a proxy objective; see value model note below)  
- **Chip-aware optimizer**: incorporates chip constraints and suggests best chip/no-chip decision for this round, plus “hold value” of saving a chip

**Constraints**
- roster size and cost cap enforcement citeturn22view0turn21view0  
- transfer rules and penalties citeturn22view0turn29search3  
- chip rules: once per season, one per week, unlock timing for Limitless/Wildcard from Round 2 citeturn21view0turn21view1  
- Sprint vs non-Sprint calendar differences citeturn23search0turn23search16

**Value change modeling note**  
Formula 1 previously stated that driver price changes were updated to be based on performance over the previous three Grands Prix rather than only the most recent. citeturn31search3  
Because the exact 2026 pricing algorithm may still evolve, the safest product design is:
- treat asset value changes as a **time series you observe and learn**, not a hardcoded formula  
- build a supervised model that predicts next price delta from rolling performance features and asset tier, and continually recalibrate

### Chip strategy planner (scenario-based + calendar picks)

Your chip planner should output:
- “play / don’t play” recommendation with a confidence score  
- top candidate weeks (calendar-driven) and what signals would “confirm” or “veto” the chip

Below are **top-3 candidate rounds per chip** for 2026, grounded in official unlock rules, Sprint calendar structure, and chip mechanics.

**Limitless (Round ≥2)**
- Best structural fit: Sprint weekends because you have an extra scoring session, and Limitless lets you stack the best assets without cap constraints. citeturn21view0turn23search0  
Top candidates:
- entity["sports_event","Chinese Grand Prix","2026 shanghai sprint"] (Round 2; earliest eligibility) citeturn21view0turn23search0  
- entity["sports_event","British Grand Prix","2026 silverstone sprint"] (mid-season once performance tiers stabilize; Sprint weekend) citeturn23search0turn23search16  
- entity["sports_event","Singapore Grand Prix","2026 singapore sprint"] (Sprint weekend; often higher randomness in street-style layouts—treat as a variance play) citeturn23search0turn23search16  
Pitfall to highlight in-app: a Limitless week still carries DSQ / not-classified downside; No Negative is a separate chip and cannot be combined the same week. citeturn21view0turn29search3

**3x Boost**
Official strategist guidance notes that 3x Boost is an optimal chip “on Sprint weekends” because you get an additional scoring session. citeturn26search15turn23search0  
Top candidates:
- entity["sports_event","Miami Grand Prix","2026 miami sprint"] (Sprint weekend; tends to be strategy-variant) citeturn23search0turn23search16  
- entity["sports_event","Dutch Grand Prix","2026 zandvoort sprint"] (Sprint weekend; track-position sensitivity can amplify qualifying and clean execution) citeturn23search0turn23search16  
- British GP (Sprint weekend) as above citeturn23search0turn26search15  
Execution rule: do not “force” 3x Boost early if the dominant team/driver is unclear under new regs; your app should compute the “option value” of waiting (expected regret reduction once confidence improves). citeturn21view0turn22view0  

**No Negative**
Purpose: downside protection when penalties and negative deltas are likely. Official definition includes “DNFs, positions lost.” citeturn21view0turn20search0  
Top candidates (risk-based):
- Singapore GP (Sprint weekend; two scoring sessions where negative outcomes can hit, and Sprint DNF/NC is explicitly a penalty category even if reduced) citeturn23search0turn22view0  
- entity["sports_event","Monaco Grand Prix","2026 monaco"] (track-position event where penalties and incidents can swing outcomes; Final Fix can also be valuable here) citeturn23search16turn26search12  
- entity["sports_event","Azerbaijan Grand Prix","2026 baku"] (historically volatile; treat as a high-variance candidate—model-based trigger should decide) citeturn23search16  
In-app trigger: “predicted probability of any roster slot scoring < 0” exceeds threshold (e.g., 35–45%), and forecast volatility is high.

**Wildcard (Round ≥2)**
Purpose: cost-cap-constrained reset with unlimited transfers, best used when you need to rebase the team after early information or a major upgrade cycle. citeturn21view0turn21view1  
Top candidates:
- after Round 2 China (post-first Sprint signals) citeturn23search0turn21view0  
- after Round 4 entity["sports_event","Bahrain Grand Prix","2026 sakhir"] (early-season stabilization point) citeturn23search16  
- after Round 9 entity["sports_event","Barcelona-Catalunya Grand Prix","2026 barcelona"] (often a major upgrade window across F1; treat as “rebase after upgrades” if confirmed by news ingestion) citeturn23search16

**Final Fix**
Purpose: post-deadline correction—replace one driver before race start (especially valuable when qualifying reveals unexpectedly strong/weak pace, or when penalties emerge after lock). citeturn21view0turn21view2  
Top candidates:
- Monaco GP (qualifying is crucial; official strategist content has historically flagged Final Fix as relevant) citeturn26search12turn23search16  
- Singapore GP (Sprint weekend; compressed schedule and variability) citeturn23search0turn23search16  
- entity["sports_event","Italian Grand Prix","2026 monza"] (high-speed, penalty/upgrades can bite; model-based trigger) citeturn23search16  

**Autopilot**
Purpose: resolve uncertainty about which driver will be top scorer by automatically assigning the 2x boost. citeturn21view0turn25search0  
Top candidates: early-season new-regs uncertainty weeks or weekends where two top teams look close (your app should compute entropy of top-scorer distribution and recommend Autopilot when entropy is high).

### Weekend intelligence checklist (what matters every race week)

Implement as a single “Race Week Briefing” page that merges structured data + parsed news + model deltas.

**Calendar + format**
- Is it a Sprint weekend? (China, Miami, Canada, Great Britain, Netherlands, Singapore) citeturn23search0  
- Session schedule and lock countdown (drive from official calendar + event hub pages) citeturn23search16turn23search22  

**Weather**
- Ingest OpenF1 weather observations (minute-level) when sessions start; reconcile with forecast API before sessions (build a “forecast vs observed” consistency metric). citeturn32view0  

**Penalties + DSQ risk**
- Grid penalties and technical scrutiny can swing “positions gained/lost” and DSQ outcomes; track these in a structured “penalty events” table and rerun sims when they change. Disqualification is a defined concept in F1’s broader rules ecosystem and exists as a fantasy penalty. citeturn30search23turn29search3  

**Reliability**
- Compute rolling not-classified hazard by constructor and driver; increase early-season uncertainty due to new regs (modeling choice anchored to official “new era” uncertainty framing). citeturn21view0  

**Track traits**
- “Passability” score: expected overtakes and positions gained potential  
- safety car likelihood proxy: derived from race_control events history citeturn32view3  
- pit stop importance proxy: pit lane loss time (derive from historical); combined with pit stop scoring buckets citeturn27search0  

**Session signals**
- FP: long-run vs short-run pace divergence  
- Quali: Q3 reach probability / constructor “both in Q3” likelihood (important because constructors get a +10 for both in Q3) citeturn17search0  

## System design for a React and Python webapp

### Architecture overview

A pragmatic 2026 build should be a **single-tenant → multi-tenant-ready** architecture:

- Frontend: React + TypeScript (charts, optimizer UI, comparison views)
- Backend: Python + FastAPI (REST endpoints for projections, optimization, league tools)
- Data jobs: scheduler (Celery + Redis or a lightweight orchestrator) for ingestion + simulation triggers
- Storage: Postgres (canonical), Redis (cache), object storage (Parquet/JSON for simulation runs)
- Observability: structured logs + metrics + tracing (OpenTelemetry-compatible stack)
- Auth: start with passwordless / magic link for personal use, extend to OAuth later

### Text diagram (services + data flow)

```
                ┌───────────────────────────┐
                │        React UI           │
                │ Team Builder / Chips /    │
                │ Sims / Reports / Alerts   │
                └─────────────┬─────────────┘
                              │ HTTPS (REST)
                              ▼
                 ┌──────────────────────────┐
                 │        FastAPI API        │
                 │  /projections /optimize   │
                 │  /lineups /league         │
                 │  /briefing /audit         │
                 └───────┬─────────┬────────┘
                         │         │
                 Cache   │         │ DB (SQL)
                (Redis)  │         ▼
                         │   ┌───────────────┐
                         │   │   Postgres     │
                         │   │ rules, assets, │
                         │   │ results, runs  │
                         │   └───────┬───────┘
                         │           │
                         ▼           ▼
          ┌────────────────────┐   ┌────────────────────┐
          │ Ingestion Workers   │   │ Simulation Workers  │
          │ OpenF1 / FastF1     │   │ Monte Carlo + opt   │
          └───────┬────────────┘   └─────────┬──────────┘
                  │                          │
                  ▼                          ▼
        ┌──────────────────┐      ┌──────────────────────┐
        │ Raw + Features    │      │ Simulation Artifacts  │
        │ (DB + Parquet)    │      │ (Object Storage)      │
        └──────────────────┘      └──────────────────────┘
```

### Pipeline triggers you should support

Because 2026 includes Sprint weekends and compressed decision windows, the backend must support event-based reruns:

- calendar-based: “48h before lock,” “after FP,” “after Quali,” “after Sprint”  
- data-based: new weather regime detected from OpenF1 weather, safety car/incident signals, penalty news items citeturn32view0turn32view3  

### Caching and performance

The expensive computation is Monte Carlo + lineup optimization. Cache at three layers:

- per-round asset projections (keyed by ruleset + model version + data cutoff)  
- per-user optimizer results (keyed by budget/constraints/chips)  
- per-page computed aggregates (leaderboards, lineups)

## Database and table design for update-friendly season-long operation

### Design principles

- Every table row should include: `source`, `source_url` (optional), `fetched_at`, `valid_from`, `valid_to` (optional), `checksum`, `version`.  
- Partition “big fact” tables by season and session (or by date) for performance.  
- Treat fantasy rules as versioned configuration, because the official rules page explicitly contains “What’s New” sections and can evolve. citeturn15search0turn22view0

### Core schemas (DDL-like; adapt as needed)

```sql
-- Reference
create table seasons (
  season int primary key,
  name text not null,
  created_at timestamptz not null default now()
);

create table circuits (
  circuit_id bigserial primary key,
  name text not null,
  country text,
  city text,
  latitude double precision,
  longitude double precision,
  source text,
  fetched_at timestamptz
);

create table meetings (
  meeting_id bigserial primary key,
  season int references seasons(season),
  round int not null,
  official_name text,
  grand_prix_name text,
  country text,
  city text,
  is_sprint boolean not null default false,
  start_date date,
  end_date date,
  source text,
  fetched_at timestamptz,
  unique (season, round)
);

create table sessions (
  session_id bigserial primary key,
  meeting_id bigint references meetings(meeting_id),
  session_key bigint,            -- link to OpenF1 session_key if used
  session_type text,             -- FP1/FP2/Quali/Sprint/Race/Sprint Qualifying
  date_start timestamptz,
  date_end timestamptz,
  source text,
  fetched_at timestamptz
);

create table drivers (
  driver_id bigserial primary key,
  driver_number int,
  full_name text,
  team_name text,
  source text,
  fetched_at timestamptz
);

create table constructors (
  constructor_id bigserial primary key,
  name text not null,
  source text,
  fetched_at timestamptz
);

-- Fantasy ruleset versioning
create table fantasy_ruleset_versions (
  ruleset_id bigserial primary key,
  season int references seasons(season),
  rules_hash text not null,
  effective_from timestamptz not null,
  source text,
  fetched_at timestamptz,
  rules_json jsonb not null
);

-- Prices (snapshots)
create table fantasy_assets (
  season int references seasons(season),
  round int not null,
  asset_type text not null,       -- 'driver' or 'constructor'
  asset_ref_id bigint not null,   -- driver_id or constructor_id (app-level id)
  price_millions numeric(6,2) not null,
  fetched_at timestamptz not null,
  source text,
  primary key (season, round, asset_type, asset_ref_id, fetched_at)
);

-- User roster history
create table fantasy_team (
  team_id bigserial primary key,
  user_id text not null,
  season int references seasons(season),
  round int not null,
  ruleset_id bigint references fantasy_ruleset_versions(ruleset_id),
  drivers jsonb not null,         -- 5 driver_ids
  constructors jsonb not null,    -- 2 constructor_ids
  boost_driver_id bigint,
  chip_used text,
  submitted_at timestamptz,
  unique (user_id, season, round)
);

create table fantasy_transfers (
  transfer_id bigserial primary key,
  user_id text not null,
  season int references seasons(season),
  round int not null,
  out_assets jsonb not null,
  in_assets jsonb not null,
  transfer_count int not null,
  penalty_points int not null default 0,
  computed_with_net_transfers boolean not null default true,
  computed_at timestamptz not null default now()
);

create table fantasy_chip_usage (
  user_id text not null,
  season int references seasons(season),
  chip_name text not null,
  round int not null,
  used_at timestamptz not null default now(),
  primary key (user_id, season, chip_name)
);

-- Results / telemetry
create table session_results (
  session_key bigint,
  driver_number int,
  position int,
  status text,
  points numeric,
  source text,
  fetched_at timestamptz,
  primary key (session_key, driver_number, fetched_at)
);

create table laps (
  session_key bigint,
  driver_number int,
  lap_number int,
  lap_duration numeric,
  sector1 numeric,
  sector2 numeric,
  sector3 numeric,
  is_pit_out_lap boolean,
  source text,
  fetched_at timestamptz,
  primary key (session_key, driver_number, lap_number, fetched_at)
);

create table weather_observations (
  session_key bigint,
  date_utc timestamptz,
  air_temp numeric,
  track_temp numeric,
  wind_speed numeric,
  wind_direction int,
  humidity int,
  rainfall numeric,
  source text,
  fetched_at timestamptz,
  primary key (session_key, date_utc)
);

create table race_control_events (
  session_key bigint,
  date_utc timestamptz,
  category text,
  flag text,
  message text,
  driver_number int,
  lap_number int,
  source text,
  fetched_at timestamptz,
  primary key (session_key, date_utc, message)
);

-- Modeling
create table model_features (
  season int,
  round int,
  entity_type text,          -- driver/constructor
  entity_id bigint,
  features jsonb,
  computed_at timestamptz,
  model_version text,
  primary key (season, round, entity_type, entity_id, model_version)
);

create table predictions (
  season int,
  round int,
  entity_type text,
  entity_id bigint,
  dist_summary jsonb,        -- mean/p10/p50/p90, etc.
  scenario_summaries jsonb,
  computed_at timestamptz,
  model_version text,
  ruleset_id bigint,
  primary key (season, round, entity_type, entity_id, model_version, computed_at)
);

create table simulation_runs (
  run_id bigserial primary key,
  season int,
  round int,
  ruleset_id bigint,
  model_version text,
  n_sims int,
  data_cutoff timestamptz,
  created_at timestamptz not null default now(),
  artifacts_uri text
);
```

### Update cadence (operational plan)

- **Calendar + sprint flags**: daily refresh (or on publish changes) from official schedule + sprint calendar pages. citeturn23search16turn23search0  
- **OpenF1 sessions**: daily refresh (docs indicate sessions updated at midnight UTC). citeturn32view1  
- **OpenF1 weather**: during live weekends, poll at least once per minute (docs: updated every minute). citeturn32view0  
- **Race control**: poll more frequently during live sessions when available; otherwise ingest after session end. citeturn32view3  
- **Simulations**: trigger on schedule and on major deltas (Quali result posted, Sprint completed, weather regime shift, penalty event detected).

## Research-to-coding handoff package and AI/agent extensions

### App requirements (testable)

- Compute official fantasy scoring for every session type (Qualifying/Sprint/Race) for drivers and constructors, including pit stop buckets and session bonuses. citeturn30search1turn29search0turn27search0turn28search0  
- Enforce roster constraints (5 drivers, 2 constructors, cost cap) and show remaining cap. citeturn22view0  
- Implement transfers with net-transfer counting and penalty handling. citeturn22view0turn29search3  
- Implement chips with correct constraints (once/season, one/week, Round-2 unlock for Limitless/Wildcard) and scoring transforms. citeturn21view0turn21view1  
- Run Monte Carlo race-week simulations (>=10,000 draws) and return distribution summaries per asset and per lineup.  
- Provide optimizer modes (EV/upside/downside/value/chip-aware) and return top-N lineups with explanations.  
- Provide a “Race Week Briefing” that fuses weather, penalties, upgrades/news, and model deltas. citeturn32view0turn22view0  
- Support Sprint detection and lock countdowns driven from official calendar data. citeturn23search0turn23search16  

### API contract (high-level shapes)

- `GET /api/v1/calendar?season=2026` → rounds, sprint flags, lock times  
- `GET /api/v1/ruleset/current` → ruleset JSON + hash + effective date  
- `GET /api/v1/assets/prices?season=2026&round=R` → price snapshots  
- `POST /api/v1/simulations/run` (round, assumptions) → run_id  
- `GET /api/v1/simulations/{run_id}/predictions` → per-asset distributions  
- `POST /api/v1/optimize` (budget, constraints, chip_state, risk_mode) → ranked lineups + distributions  
- `GET /api/v1/briefing?season=2026&round=R` → checklist + key deltas + recommended actions  
- `GET /api/v1/audit/lineup?season=2026&round=R` → points breakdown ledger for explainability

### Simulation pseudocode (backend)

```text
build_feature_frame(round):
  ingest OpenF1 sessions/laps/weather/race_control
  compute pace features, reliability features, track traits, scenario priors
  return features_by_driver, features_by_constructor

run_monte_carlo(round, n_sims):
  feats = build_feature_frame(round)
  for sim in 1..n_sims:
    scenario = sample(weather_regime, safety_car_regime, grid_uncertainty)
    outcomes = simulate_finish_and_events(feats, scenario)
    points = apply_fantasy_rules(outcomes, ruleset, chip=None)
    accumulate(points)
  summarize_distributions()
  persist(run_metadata + summaries)
  return summaries
```

### UI page map (MVP → V1)

MVP pages:
- Dashboard (next lock countdown, sprint flag, quick recommendations)
- Team Builder (with optimizer modes)
- Projections (asset distributions + breakdown)
- Chip Planner (calendar + scenarios)
- Race Week Briefing (checklist + alerts)
- Score Audit (how points were computed)

### Backlog (MVP → V1 → V2)

MVP:
- scoring engine, ingestion, baseline simulator, basic optimizer, team builder UI

V1:
- opponent-aware mode, better reliability model, race-week briefing generator, alerting

V2:
- automated news/social agents, anomaly detection, full “season planner” with lookahead optimization

### AI / agent ideas that actually help you win

Because the biggest edge in F1 Fantasy is reacting faster (but correctly) to new information, agents should be scoped to **actionable** signals with source-quality scoring.

**News agent (official + reputable sources)**
- monitors Formula 1 site for strategist previews, schedule changes, and weekend info (including weather forecast articles and Sprint calendar posts) citeturn21view0turn23search0turn23search16  
- extracts: penalties, upgrades, reliability hints, expected weather shifts  
- outputs: structured “news events” with confidence and provenance

**Social agent (high-signal filtering)**
- ingest short-form updates from known reporters/teams; dedupe by semantic similarity; rank by “fantasy impact” (grid penalty, component change, rain, driver illness)  
- never treat social as ground truth; require confirmation or maintain “unconfirmed” state

**Auto-briefing generator**
- “What changed since last sim run?”  
- “Top 3 lineups by safe / balanced / upside”  
- “Chip recommendation yes/no and why,” referencing the official chip mechanics and sprint structure citeturn21view0turn26search15turn23search0  

**Anomaly detector**
- flags practice pace outliers, sudden lap-time deltas, unusual incident frequency from race_control, and weather regime shifts from OpenF1 weather citeturn32view3turn32view0  

**Real-time access fallback**
- if real-time OpenF1 access is constrained, degrade gracefully: run “pre-lock” sims using historical + forecast; rerun immediately after key sessions end when data is available (OpenF1 provides structured session, lap, weather, and race control datasets suitable for post-session ingestion). citeturn13search24turn32view1turn32view0turn32view3