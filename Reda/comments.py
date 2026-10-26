"""Nos commentaires (cellules markdown) du notebook. Lancer ce fichier écrit comments.json, lu par build_notebook.py."""
import json
from pathlib import Path

C = {}

C['seasonal'] = r'''
**Choices.** The 29 February is removed so that every year has exactly 365 days (it only concerns 22 days out of 31 412).
The smoothing window is 31 days, centred, and *circular*: to smooth the first days of January we use the last days of
December, because the seasonal cycle is periodic.

**Comment.** The three curves follow a smooth sinusoidal cycle. The coldest period is around mid-February (day ~50,
median ≈ 7.8 °C) and the warmest around early August (day ~219, median ≈ 16.5 °C): the annual amplitude of the median
is only ≈ 9 °C, and the maximum comes about 6 weeks after the summer solstice. This small amplitude and this delay are
the signature of the **oceanic climate** of Brest: the Atlantic Ocean stores heat in summer and releases it in winter.
The spread between the 10 % and 90 % quantiles is larger in winter (≈ 7 °C) than in summer (≈ 3.5 °C): in winter,
the temperature depends strongly on the wind direction (mild oceanic air vs. cold continental air), while summers are
more regular. The 90 % curve (between ≈ 10.5 °C in winter and ≈ 18.6 °C in summer) is the threshold used below to
detect heat waves.
'''

C['heatwaves_def'] = r'''
**Definitions.** Let $T_d$ be the daily mean temperature of day $d$ and $q_{p}(j)$ the smoothed quantile of its day
of the year $j$. A day is *hot* if $T_d>q_{90}(j)$. A heat wave is a maximal run of at least $L_{\min}=3$ consecutive
hot days (the slides speak of "several consecutive days"; 3 days is a usual convention). For a wave $W$:

$$
\text{duration}=|W|\ \text{(days)},\qquad
\text{intensity}=\frac{1}{|W|}\sum_{d\in W}\big(T_d-q_{50}(j_d)\big)\ \text{(°C)},
$$

i.e. the anomaly is measured with respect to the *normal* day (smoothed median).

**Comment.** We find 421 heat waves in 86 years (≈ 5 per year). The longest ones lasted 14 days (August 1955 and August
1976, the famous drought summer). The most intense one is **July 2022** (+7.7 °C above normal for 3 days), the heat
wave during which Brittany experienced record temperatures. Because the threshold depends on the day of the year,
the definition also detects mild spells in winter (e.g. April 1945): they are anomalies *for the season*, not hot days
in absolute terms.
'''

C['scatter'] = r'''
**Comment.** Most heat waves are short (3 to 5 days) with an intensity between 2.5 and 5 °C; long waves (≥ 10 days) are
rare. There is no clear link between duration and intensity: the most intense waves are often short (a few days of
very hot continental air), while long waves are moderate. The colours show that the most intense short events
(top-left) are mainly recent (yellow: 2000s–2020s). The right panel shows the clearest signal: the **number** of heat
waves per decade decreased from the 1940s to the 1960s–1970s, then increased steadily, up to 73 waves in the 2020s,
which only contain 6 years (2020–2025). This is consistent with global warming since the 1980s. The mean duration and
intensity per decade, however, remain stable (≈ 4.3 days, ≈ 3.6 °C).

*Limit:* the quantiles are computed over the whole period 1940–2025. In a warming climate, the threshold is
"too low" for recent years and "too high" for old years, which mechanically creates more waves at the end of the
period. This is precisely the trend we want to show, but it should be kept in mind.
'''

C['yearly'] = r'''
**Comment.** The annual maximum (the hottest moment of the year, in °C) fluctuates strongly from one year to the next
(between 21.7 °C and 34.2 °C), because it depends on the weather of a few days. The 11-year rolling mean is roughly flat
until the 1980s (≈ 25 °C) and then increases by about 1.5 to 2 °C. The mean was 25.1 °C over 1940–1979 and 26.3 °C over
1980–2025, and the year-to-year variability also increased (standard deviation 1.9 °C → 2.4 °C): recent decades have
both hotter and more variable extremes. The record of the series is 2022 (34.2 °C), clearly above the previous
records (2003: 31.0 °C; 1990: 30.4 °C). Note that ERA5 values are averages over a ≈ 9 km cell that includes some sea,
so they are lower than the peaks measured by a local weather station.
'''

C['correlation'] = r'''
**Comment.** The raw correlation between the annual maximum and CO2 is weak, $r\approx0.31$: in a single year, the
weather noise dominates the climate signal. The logarithm of CO2 gives almost the same value ($r\approx0.30$), because
CO2 only varies from 310 to 428 ppm, a range where $\ln$ is almost linear (and $\ln(C/280)$ gives exactly the same $r$
as $\ln C$, since the Pearson correlation is invariant under affine transforms). Smoothing the temperature with a
rolling mean removes the year-to-year noise and increases the correlation a lot: $r=0.47$ (5 years), $0.60$ (11 years),
$0.82$ (21 years).

This high correlation does not mean that the annual maximum of a given year is predictable: it means that the
**mean level** of the extremes follows CO2, while the weather adds a large random part around it. This is exactly why
the forecast must be **probabilistic**: the model should predict how the *distribution* of the annual maximum moves
with CO2. We keep $\ln(C/C_0)$ as the covariate, because the radiative forcing of CO2 is logarithmic, which matters
when we extrapolate up to 946 ppm.
'''

C['model'] = r'''
**Comment on the validation.** Trained on 1940–2000 only, our model gets a CRPS of **1.66 °C** on 2001–2025, better than
a linear trend with Gaussian noise (1.70 °C) and than the constant climate of 1940–2000 (1.82 °C). The forecasts are
therefore better than simply assuming that the climate does not change. The gain over the Gaussian model is modest:
with 25 test years, the difference between two reasonable models is small.

**Comment on the parameters (fit on 1940–2025).** $\hat\beta_1\approx5.9$ °C per unit of $\ln$ CO2: from 1940 (310 ppm)
to 2025 (428 ppm), $\ln$ CO2 increased by 0.32, i.e. a shift of $\approx1.9$ °C of the location of the annual maximum.
The bootstrap interval of $\beta_1$ is wide ([1.6, 10.4] °C): the trend is clearly positive, but its size is uncertain
with 86 years, and this uncertainty is propagated to the forecasts. $\hat\sigma\approx1.9$ °C is the weather
variability, and $\hat\xi\approx-0.11<0$ confirms a bounded upper tail.
'''

C['projection'] = r'''
**Comment.** The three scenarios start from the same level in 2026 (median ≈ 26.5 °C) and diverge after 2040. Under
SSP1-2.6, CO2 peaks and decreases back to 400 ppm: the median annual maximum stabilises then slightly decreases
(≈ 26.1 °C in 2100). Under SSP2-4.5 it reaches ≈ 27.8 °C, and under SSP5-8.5 (946 ppm) ≈ 31.5 °C, i.e. a typical year
of 2100 would be as hot as the hottest years of the 20th century. The 5–95 % band is wide (≈ 7 to 11 °C) because a
single year's maximum depends on the weather; it widens with time under SSP5-8.5, because the uncertainty on the
CO2 sensitivity $\beta_1$ is multiplied by a larger CO2 increase.
'''

C['dist2100'] = r'''
**Answer: probability of exceeding 40 °C in Brest.** The question can be read in two ways, so we give both:

| Scenario | CO2 2100 | median 2100 | P(year 2100 > 40 °C) | P(at least one year > 40 °C in 2026–2100) |
|---|---|---|---|---|
| SSP1-2.6 | 400 ppm | 26.1 °C | ≈ 0.01 % | ≈ 0.3 % |
| SSP2-4.5 | 527 ppm | 27.8 °C | ≈ 0.02 % | ≈ 0.7 % |
| SSP5-8.5 | 946 ppm | 31.5 °C | ≈ 0.75 % | ≈ 8 % |

**Comment.** In the ERA5 data, exceeding 40 °C in Brest remains very unlikely in a given year, even in 2100 under the
worst scenario (< 1 %). But over the 75 years until 2100, the risk accumulates: under SSP5-8.5, there is about
**1 chance in 12** that at least one year exceeds 40 °C, against less than 1 % under SSP1-2.6. The choice of the
scenario, i.e. of the emissions, multiplies this risk by more than 20. With the fitted $\xi<0$, the GEV has a finite upper
bound $\mu-\sigma/\xi$ (median ≈ 43 °C for SSP1-2.6 and ≈ 50 °C for SSP5-8.5): 40 °C is physically possible in all
scenarios, but it lies far in the tail.

**Limits.** (i) The data are ERA5 cell averages (≈ 9 km, partly over the sea), which smooth the local peaks: a
weather station in Brest can be several degrees hotter than the ERA5 cell, so these probabilities concern the ERA5
variable and underestimate the risk for a station. (ii) The model only knows CO2: it ignores aerosols, changes in
atmospheric circulation or in soil moisture, which can amplify heat waves. (iii) 946 ppm is far outside the
observed range (310–428 ppm): the linear relation in $\ln$ CO2 is an extrapolation, partly controlled by the
bootstrap uncertainty. (iv) Probabilities below 0.1 % are estimated with only a few of the 10 000 members and
are therefore only orders of magnitude.
'''

C['minima'] = r'''
**Approach for the minima (different and non-parametric).** We keep a linear trend in $\ln$ CO2 fitted by least squares,
but no distribution is assumed for the noise: each Monte-Carlo member uses the regression fitted on a bootstrap
sample of the years, and adds residuals drawn from the observed residuals of that fit (residual bootstrap). The
predictive distribution is therefore built only from the observed anomalies.

**Comment.** The annual minimum (coldest moment of the year) is much less correlated with CO2 than the maximum
($r\approx0.15$): it is dominated by rare cold spells with continental air (1985, 1987 at −6.6 °C). Validated on
2001–2025 after training on 1940–2000, this approach gets a CRPS of 1.09 °C, close to the Gaussian baseline (1.06 °C):
the minima are hard to predict, and most of their variance is weather. In 2100 the median minimum is ≈ −0.3 °C (SSP1-2.6),
≈ +0.6 °C (SSP2-4.5) and ≈ +2.3 °C (SSP5-8.5). Over 1940–2025, 60 % of the years went below 0 °C; in 2100 this
probability falls to ≈ 54 %, 38 % and 20 % respectively: under SSP5-8.5, four years out of five would have no frost
at all in Brest. Frost does not disappear, though: over 2026–2100 every trajectory has at least one year below 0 °C.
The histograms are spiky because the noise is resampled among only 86 observed residuals.
'''

C['conclusion'] = r'''
# Conclusion

- **Past (Part 1).** Brest has a mild oceanic seasonal cycle (≈ 9 °C amplitude of the median). Heat waves, defined
  relative to the season, became much more frequent since the 1980s (73 waves in 2020–2025 alone), and the most intense
  one is July 2022.
- **Future (Part 2).** The annual maximum depends on CO2 through a weak but robust link (correlation 0.31 raw,
  0.82 after 21-year smoothing). A non-stationary GEV model trained with PyTorch, with bootstrap Monte-Carlo, beats a
  Gaussian baseline out of sample (CRPS 1.66 °C vs 1.70 °C). In 2100, the median annual maximum goes from ≈ 26 °C
  (SSP1-2.6) to ≈ 31.5 °C (SSP5-8.5). Exceeding 40 °C in a given year stays below 1 %, but the probability of at least
  one such year before 2100 reaches ≈ 8 % under SSP5-8.5, against ≈ 0.3 % under SSP1-2.6.
- **Main message.** The emission scenario strongly controls the risk of extreme heat in Brest, and the uncertainty
  (weather + model) must always be given with the forecast.
'''

(Path(__file__).parent / 'comments.json').write_text(json.dumps({k: v.strip() for k, v in C.items()}, indent=1,
                                                                ensure_ascii=False))
print('écrit : comments.json')
