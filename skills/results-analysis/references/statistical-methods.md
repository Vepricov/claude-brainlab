# Statistical Methods for ML/AI Experiments

Complete guide to statistical analysis methods for ML/AI experiment results.

## Basic Statistics

### Mean

**Definition**: Average of all observations

**Formula**: μ = (Σx) / n

**Reporting format**: "The model achieves 85.3% accuracy on the test set"

### Standard Deviation (SD)

**Definition**: Measures data dispersion

**Formula**: SD = √[Σ(x - μ)² / (n-1)]

**Reporting format**: "Accuracy is 85.3% ± 2.1% (standard deviation)"

**When to use**: Describing data variability

### Standard Error (SE)

**Definition**: Standard deviation of the sample mean

**Formula**: SE = SD / √n

**Reporting format**: "Accuracy is 85.3% ± 0.7% (standard error)"

**When to use**: Estimating uncertainty of the mean

### Standard Deviation vs. Standard Error

| Property | Standard Deviation (SD) | Standard Error (SE) |
|------|------------|------------|
| Meaning | Data dispersion | Uncertainty of mean estimate |
| Changes with sample size | Stable | Decreases (∝ 1/√n) |
| Use | Describing data variability | Inferring population mean |
| Reporting context | Descriptive statistics | Inferential statistics |

**Important**: Papers must clearly state whether SD or SE is being used.

### Confidence Interval (CI)

**Definition**: Possible range of a population parameter

**95% confidence interval formula**: CI = μ ± t(α/2, n-1) × SE

**Reporting format**: "Accuracy is 85.3% [95% CI: 83.9%, 86.7%]"

**Interpretation**: A 95% confidence interval means that if the experiment is repeated many times, 95% of the intervals will contain the true value.

## Prerequisite Tests (Must Be Performed)

Before conducting parametric tests, verify that the data meets the assumptions of the test.

### 1. Normality Test

**Purpose**: Verify whether data follows a normal distribution

**When needed**: Before using t-test, ANOVA, and other parametric tests

**Common methods**:

#### Shapiro-Wilk Test
- **Applicable**: Sample size n < 50
- **Null hypothesis**: Data follows a normal distribution
- **Judgment**: p > 0.05 → Accept normality assumption
- **Use case**: Small samples, most commonly used

#### Kolmogorov-Smirnov Test
- **Applicable**: Sample size n >= 50
- **Null hypothesis**: Data follows a normal distribution
- **Judgment**: p > 0.05 → Accept normality assumption
- **Use case**: Large samples

#### Anderson-Darling Test
- **Applicable**: All sample sizes
- **Advantage**: More sensitive to tail deviations
- **Use case**: When tail anomalies need to be detected

#### Q-Q Plot (Quantile-Quantile Plot)
- **Type**: Graphical method
- **Judgment**: Points near a straight line → Normal distribution
- **Advantage**: Intuitively shows degree of deviation
- **Use case**: Used together with numerical tests

**When normality is not met**:
1. Data transformation (log, sqrt, Box-Cox)
2. Use non-parametric tests (Wilcoxon, Mann-Whitney U)
3. Increase sample size (Central Limit Theorem)

### 2. Homogeneity of Variance Test

**Purpose**: Verify whether the variances of multiple groups are equal

**When needed**: Before using independent samples t-test, ANOVA

**Common methods**:

#### Levene's Test
- **Applicable**: Most commonly used, robust to non-normal distributions
- **Null hypothesis**: Variances of all groups are equal
- **Judgment**: p > 0.05 → Accept homogeneity of variance assumption
- **Use case**: Default choice

#### Bartlett's Test
- **Applicable**: When data strictly follows a normal distribution
- **Null hypothesis**: Variances of all groups are equal
- **Judgment**: p > 0.05 → Accept homogeneity of variance assumption
- **Use case**: When normality is already verified

#### Brown-Forsythe Test
- **Applicable**: Improved version of Levene's test
- **Advantage**: More robust to non-normal distributions
- **Use case**: When data is clearly skewed

**When homogeneity of variance is not met**:
1. Use Welch's t-test (does not assume equal variances)
2. Use Welch's ANOVA
3. Data transformation
4. Use non-parametric tests

### 3. Independence Test

**Purpose**: Verify whether observations are independent of each other

**When needed**: Before all statistical tests

**Common violations of independence**:
- Time series data (autocorrelation)
- Repeated measurements (same object measured multiple times)
- Clustered data (observations within the same group)

**Handling methods**:
- Time series: Use time series analysis methods
- Repeated measurements: Use paired tests or mixed effects models
- Clustered data: Use multilevel models or cluster-robust standard errors

### 4. Outlier Detection

**Purpose**: Identify and handle extreme values

**Common methods**:

#### IQR Method
- **Definition**: Outlier = outside Q1 - 1.5×IQR or Q3 + 1.5×IQR
- **Use case**: Most common, simple and intuitive

#### Z-score Method
- **Definition**: |Z| > 3 is an outlier
- **Use case**: Data approximately normally distributed

#### Grubbs' Test
- **Applicable**: Detecting a single outlier
- **Use case**: Normally distributed data

**Handling outliers**:
1. Check if it's a data error
2. Report the presence of outliers
3. Conduct sensitivity analysis (with/without outliers)
4. Use robust statistical methods

## Prerequisite Test Decision Tree

```
Start
  |
  v
Sample size < 30?
  | Yes
  v
  Check normality (Shapiro-Wilk)
    | Not met
    v
    Use non-parametric tests
  | No
  v
  Check normality (K-S or Q-Q plot)
    | Met
    v
    Two groups comparison?
      | Yes
      v
      Check homogeneity of variance (Levene)
        | Met
        v
        Independent samples t-test
        | Not met
        v
        Welch's t-test
      | No
      v
      Multiple groups comparison?
        | Yes
        v
        Check homogeneity of variance (Levene)
          | Met
          v
          ANOVA
          | Not met
          v
          Welch's ANOVA
```

## Prerequisite Test Reporting Template

**Report in the paper**:

"Before conducting parametric tests, we verified data normality using the Shapiro-Wilk test (Method A: W = 0.96, p = 0.23; Method B: W = 0.95, p = 0.18) and homogeneity of variance using Levene's test (F = 1.23, p = 0.31). All tests met the assumptions for parametric testing."

**If assumptions are not met**:

"The Shapiro-Wilk test showed data does not meet the normality assumption (Method A: W = 0.87, p = 0.01), so we used the non-parametric Mann-Whitney U test for comparison."

## Hypothesis Testing (Parametric Tests)

### 1. t-test (Two Group Comparison)

**Purpose**: Compare performance differences between two methods

**Assumptions**:
- Data follows a normal distribution
- Homogeneity of variance (independent samples t-test)
- Independent observations

#### Independent Samples t-test

**Use case**: Comparing means of two independent groups
- Example: Method A vs. Method B performance on different datasets

**Hypotheses**:
- H₀: μ₁ = μ₂ (means of two groups are equal)
- H₁: μ₁ ≠ μ₂ (means of two groups are not equal)

**Reporting format**: "Method A (85.3% ± 2.1%) significantly outperforms Method B (82.1% ± 1.8%), t(18) = 3.45, p = 0.003"

**When to use**: Two independent groups, meeting normality and homogeneity of variance

#### Paired Samples t-test

**Use case**: Comparing the performance of the same group under two conditions
- Example: Method A vs. Method B performance on the same dataset

**Hypotheses**:
- H₀: μd = 0 (mean of differences is 0)
- H₁: μd ≠ 0 (mean of differences is not 0)

**Reporting format**: "On 10 datasets, Method A significantly outperforms Method B, t(9) = 4.23, p = 0.002"

**When to use**: Paired data, before-and-after comparison of the same object

#### Welch's t-test

**Use case**: When the variances of two groups are unequal
- Example: When the homogeneity of variance test fails (Levene's test p < 0.05)

**Advantage**: Does not assume equal variances, more robust

**Reporting format**: "Method A significantly outperforms Method B, Welch's t(16.3) = 3.21, p = 0.005"

**When to use**: Alternative when homogeneity of variance test fails

### 2. ANOVA (Multiple Group Comparison)

**Purpose**: Compare three or more methods simultaneously

**Assumptions**:
- Data follows a normal distribution
- Homogeneity of variance
- Independent observations

#### One-Way ANOVA

**Use case**: Comparing means of multiple independent groups
- Example: Method A vs. B vs. C vs. D performance comparison

**Hypotheses**:
- H₀: μ₁ = μ₂ = μ₃ = ... = μk (all group means are equal)
- H₁: At least one group mean is different

**Reporting format**: "Significant differences exist between methods, F(3, 36) = 8.45, p < 0.001"

**When to use**: Three or more independent groups

**Important**: ANOVA only tells you "at least one group is different"; post-hoc tests are needed to find out which groups differ.

#### Repeated Measures ANOVA

**Use case**: Performance of the same group under multiple conditions
- Example: Performance of multiple methods on the same dataset

**Hypotheses**:
- H₀: Means under all conditions are equal
- H₁: At least one condition's mean is different

**Reporting format**: "Significant differences exist between methods, F(3, 27) = 12.34, p < 0.001"

**When to use**: Paired data, comparison of multiple conditions

#### Two-Way ANOVA

**Use case**: Studying the effects of two factors and their interaction
- Example: Effect of method type (factor 1) × dataset size (factor 2) on performance

**Reporting format**:
- "Main effect of method type is significant, F(2, 54) = 15.23, p < 0.001"
- "Main effect of dataset size is significant, F(2, 54) = 8.91, p < 0.001"
- "Interaction is not significant, F(4, 54) = 1.23, p = 0.31"

**When to use**: Studying multiple factors and their interactions

#### Welch's ANOVA

**Use case**: Alternative to ANOVA when variances are unequal

**Reporting format**: "Significant differences exist between methods, Welch's F(3, 18.5) = 7.89, p = 0.002"

**When to use**: When homogeneity of variance test fails

### 3. Post-hoc Tests

**Purpose**: After ANOVA is significant, find which groups specifically differ

**Common methods**:

#### Tukey HSD (Honestly Significant Difference)

**Use case**: Standard post-hoc test after ANOVA
- **Advantage**: Controls family-wise error rate
- **Applicable**: Equal or similar group sample sizes
- **Reporting**: "Tukey HSD test shows Method A significantly outperforms Method B (p = 0.003) and Method C (p = 0.012)"

**When to use**: Default choice, most commonly used

#### Bonferroni Correction

**Use case**: Conservative post-hoc test
- **Advantage**: Simple, controls family-wise error rate
- **Disadvantage**: Too conservative
- **Reporting**: "After Bonferroni correction, Method A significantly outperforms Method B (p = 0.002)"

**When to use**: When strict control of Type I error is needed

#### Scheffé's Test

**Use case**: Most conservative post-hoc test
- **Advantage**: Applies to all contrasts (including complex contrasts)
- **Disadvantage**: Lowest power
- **Reporting**: "Scheffé's test shows Method A significantly outperforms Method B (p = 0.015)"

**When to use**: When complex contrasts are needed

#### Dunnett's Test

**Use case**: Comparing multiple experimental groups with one control group
- **Advantage**: Specifically designed for comparison with a control group
- **Reporting**: "Dunnett's test shows Methods A, B, C all significantly outperform the baseline (p < 0.01)"

**When to use**: When there is a clear control group (baseline method)

## Hypothesis Testing (Non-Parametric Tests)

**When to use non-parametric tests**:
- Data does not meet normality assumptions
- Very small sample size (n < 30)
- Data is ordinal or ranked
- Presence of obvious outliers

### 4. Wilcoxon Test (Paired Data)

**Purpose**: Non-parametric test for paired data; non-parametric alternative to t-test

**Use case**: Performance comparison of two methods on the same dataset
- Example: Method A vs. Method B on 10 datasets

**Hypotheses**:
- H₀: Medians of the two groups are equal
- H₁: Medians of the two groups are not equal

**Reporting format**: "Wilcoxon signed-rank test shows Method A significantly outperforms Method B, Z = 2.81, p = 0.005"

**When to use**: Paired data, does not meet normality assumptions

### 5. Mann-Whitney U Test (Independent Data)

**Purpose**: Non-parametric test for independent samples; non-parametric alternative to independent samples t-test

**Use case**: Performance comparison of two independent groups
- Example: Method A on dataset 1 vs. Method B on dataset 2

**Hypotheses**:
- H₀: Distributions of the two groups are the same
- H₁: Distributions of the two groups are different

**Reporting format**: "Mann-Whitney U test shows Method A significantly outperforms Method B, U = 45, p = 0.012"

**When to use**: Independent samples, does not meet normality assumptions

**Also known as**: Wilcoxon rank-sum test

### 6. Kruskal-Wallis Test (Multiple Groups)

**Purpose**: Non-parametric test for multiple independent samples; non-parametric alternative to ANOVA

**Use case**: Performance comparison of three or more methods
- Example: Method A vs. B vs. C vs. D

**Hypotheses**:
- H₀: Distributions of all groups are the same
- H₁: At least one group's distribution is different

**Reporting format**: "Kruskal-Wallis test shows significant differences between methods, H(3) = 15.23, p = 0.002"

**When to use**: Multiple independent samples, does not meet normality assumptions

**Post-hoc test**: Dunn's test (with Bonferroni correction)

### 7. Friedman Test (Repeated Measures)

**Purpose**: Non-parametric test for multiple groups with paired data; non-parametric alternative to repeated measures ANOVA

**Use case**: Performance comparison of multiple methods on the same dataset
- Example: Method A vs. B vs. C vs. D on 10 datasets

**Hypotheses**:
- H₀: Distributions under all conditions are the same
- H₁: At least one condition's distribution is different

**Reporting format**: "Friedman test shows significant differences between methods, χ²(3) = 18.45, p < 0.001"

**When to use**: Paired data, multiple groups comparison, does not meet normality assumptions

**Post-hoc test**: Nemenyi test or Wilcoxon signed-rank test (with Bonferroni correction)

### 8. Sign Test

**Purpose**: Simplest non-parametric test for paired data

**Use case**: Only care about direction (which is better), not the magnitude of the difference
- Example: On how many datasets does Method A outperform Method B

**Hypotheses**:
- H₀: Numbers of positive and negative differences are equal
- H₁: Numbers of positive and negative differences are not equal

**Reporting format**: "Sign test shows Method A outperforms Method B on 8 out of 10 datasets, p = 0.055"

**When to use**: Only care about wins/losses, not the magnitude of the difference

**Advantage**: Most robust, not sensitive to outliers
**Disadvantage**: Lowest power

## Statistical Test Selection Flowchart

```
Data type?
  |
  v
Paired data?
  | Yes
  v
  Two groups comparison?
    | Yes
    v
    Normality test
      | Met
      v
      Paired t-test
      | Not met
      v
      Wilcoxon signed-rank test
    | No (multiple groups)
    v
    Normality test
      | Met
      v
      Repeated measures ANOVA
      | Not met
      v
      Friedman test
  | No (independent data)
  v
  Two groups comparison?
    | Yes
    v
    Normality test
      | Met
      v
      Homogeneity of variance test
        | Met
        v
        Independent t-test
        | Not met
        v
        Welch's t-test
      | Not met
      v
      Mann-Whitney U test
    | No (multiple groups)
    v
    Normality test
      | Met
      v
      Homogeneity of variance test
        | Met
        v
        ANOVA + post-hoc tests
        | Not met
        v
        Welch's ANOVA + Games-Howell
      | Not met
      v
      Kruskal-Wallis + Dunn's test
```

## Multiple Comparison Correction

**Problem**: Multiple tests increase Type I error (false positive) probability

**Formula**: P(at least one error) = 1 - (1-α)^k, where k is the number of tests

**Common methods**:

| Method | Formula | Conservative Level | Use Case |
|------|------|----------|----------|
| Bonferroni | α' = α/k | Most conservative | Few tests |
| Holm-Bonferroni | Stepwise correction | Moderately conservative | Medium number of tests |
| FDR (Benjamini-Hochberg) | Controls false discovery rate | Less conservative | Many tests, exploratory analysis |

## Effect Size

**Definition**: Measures the actual magnitude of the difference, independent of sample size

**Common metrics**:

| Effect Size | Applicable Scenario | Interpretation |
|--------|----------|------|
| Cohen's d | t-test | \|d\| < 0.2 small, 0.2-0.5 medium, >=0.8 large |
| η² (Eta squared) | ANOVA | 0.01 small, 0.06 medium, 0.14 large |
| r (correlation coefficient) | Non-parametric tests | 0.1 small, 0.3 medium, 0.5 large |

**Reporting**: Must report both p-value and effect size

## Experimental Design Key Points

**Number of repetitions**: At least 3-5 times, recommended 5-10 times, 10+ for high-variance tasks

**Random seeds**: Report all random seeds used to ensure reproducibility

**Cross-validation**: k-fold (k=5 or 10) for evaluating generalization performance

## Common Errors

1. **Cherry-picking**: Only reporting best results → Report all experiments
2. **p-hacking**: Trying multiple analyses to find significant results → Pre-specify methods
3. **Confusing SD and SE**: Not stating which is used → Label explicitly
4. **Ignoring multiple comparisons**: Not correcting for multiple tests → Use Bonferroni/FDR
5. **Only reporting p-value**: Missing effect size → Report both

## Reporting Checklist

- [ ] Report mean and standard deviation/standard error (labeled explicitly)
- [ ] Report number of experimental repetitions
- [ ] Perform prerequisite tests (normality, homogeneity of variance)
- [ ] Select appropriate statistical test
- [ ] Report complete statistical information (test statistic, degrees of freedom, p-value)
- [ ] Report effect size
- [ ] Correct for multiple comparisons
- [ ] State random seed settings

## Reference Resources

- [Nature Statistics Checklist](https://www.nature.com/documents/nr-reporting-summary-flat.pdf)
- [ASA Statement on P-Values](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf)
- [Reporting Statistics in Psychology](https://apastyle.apa.org/instructional-aids/numbers-statistics-guide.pdf)

## Summary

Core principles of statistical analysis:

1. **Prerequisite tests** - Verify assumptions
2. **Complete reporting** - Mean, SD/SE, sample size
3. **Appropriate tests** - Choose method based on data characteristics
4. **Multiple correction** - Correct α when making multiple comparisons
5. **Effect size** - Don't only report p-value
6. **Reproducible** - Provide sufficient detail

Following these principles ensures statistical rigor and credibility of experimental results.
