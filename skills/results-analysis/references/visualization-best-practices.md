# Visualization Best Practices for ML/AI Papers

Best practices guide for publication-quality visualization.

## Core Principles

1. **Clarity** - Information is conveyed clearly, without ambiguity
2. **Accuracy** - Data is represented accurately, without misleading
3. **Accessibility** - Colorblind-friendly, readable in black and white
4. **Professionalism** - Meets academic publication standards

## Figure Format Requirements

### Vector vs. Raster

| Format | Type | Use Case | Quality |
|------|------|----------|------|
| PDF/EPS | Vector | Charts, curves, diagrams | Recommended |
| SVG | Vector | Web display | Usable |
| PNG | Raster | Photos, screenshots | Needs high resolution (>=600 DPI) |
| JPG | Raster | Photos | Avoid for charts |

**Rule**: Use vector format (PDF/EPS) for all charts; use high-resolution raster (PNG >=600 DPI) for photos.

## Color Schemes

### Colorblind-Friendly Colors

**Recommended color schemes**:

#### Okabe-Ito (most commonly used)
- Orange: #E69F00
- Sky Blue: #56B4E9
- Green: #009E73
- Yellow: #F0E442
- Blue: #0072B2
- Red: #D55E00
- Pink: #CC79A7
- Black: #000000

#### Paul Tol Colors
- Suitable for qualitative data
- Multiple color scheme options (bright, muted, contrast)

### Color Principles

1. **Use at most 5-7 colors** - Too many colors are hard to distinguish
2. **Avoid red-green combinations** - Red-green colorblind cannot distinguish
3. **Test black-and-white printing** - Ensure readability in grayscale
4. **Use different line styles** - Combine with colors (solid, dashed, dotted)

## Chart Type Selection

### Line Plot

**Use cases**: Showing trends, training curves, time series

**Key points**:
- Use error bands (shaded regions) to show standard deviation/standard error
- Line width 1.5-2.0 pt
- Marker size moderate (4-6 pt)
- Grid line opacity 0.3

**Examples**: Training loss curves, accuracy vs. epoch

### Bar Plot

**Use cases**: Performance comparisons, ablation experiments

**Key points**:
- Use error bars to show uncertainty
- Consistent bar widths
- Appropriate spacing (20-30% of bar width)
- Bold the best result bar

**Examples**: Accuracy comparison of different methods

### Box Plot

**Use cases**: Showing distributions, identifying outliers

**Key points**:
- Show median, quartiles, outliers
- Suitable for showing results across multiple runs
- Can overlay with scatter plot

**Examples**: Performance distribution across multiple runs

### Scatter Plot

**Use cases**: Showing correlations, clustering results

**Key points**:
- Appropriate point size and opacity
- Use different shapes to distinguish categories
- Add trend lines (if needed)

**Examples**: Predicted vs. actual values, feature space visualization

### Heatmap

**Use cases**: Confusion matrices, correlation matrices, attention weights

**Key points**:
- Use sequential color scheme (single-color gradient) or diverging color scheme (two-color gradient)
- Add numerical labels (if space allows)
- Clearly label colorbar

**Examples**: Confusion matrices, attention visualization

## Chart Element Standards

### Axes

**X and Y axes**:
- Label font size: 10-12 pt
- Tick font size: 8-10 pt
- Labels clearly describe variable and units
- Tick spacing is reasonable

**Axis ranges**:
- Y-axis typically starts at 0 (unless there is a special reason)
- Don't truncate axes to exaggerate differences
- Use scientific notation for large values

### Legend

**Position**: Does not obscure data, typically placed in upper right or outside

**Content**:
- Concisely describes each curve/bar
- Font size 8-10 pt
- Uses same colors and line styles as in the figure

### Titles and Labels

**Figure title**: Typically do not add title inside the figure; use caption instead

**Caption**:
- Self-contained, does not depend on main text
- Explains figure content, experimental setup, key observations
- Font size 9-10 pt

**Example**: "Figure 1: Accuracy comparison of different models on the test set. Error bars indicate standard deviation over 5 runs. Our method (blue) outperforms baselines on all datasets."

## Error Representation

### Error Bars

**Types**:
- Standard Deviation (SD): Describes data variability
- Standard Error (SE): Describes uncertainty of the mean
- Confidence Interval (CI): Range of parameter estimates

**Representation methods**:
- Bar plots: Vertical error bars
- Line plots: Error bands (shaded regions)

**Must state**: Clearly indicate in caption which type of error is used

### Error Bands

**Error representation for line plots**:
- Use semi-transparent shaded region (alpha=0.2-0.3)
- Color matches the main line
- Don't use error bars (would clutter the figure)

## Sizes and Resolution

### Figure Sizes

**Single-column figures**:
- Width: 3.5 inches (approx. 9 cm)
- Height: 2-3 inches

**Double-column figures**:
- Width: 7 inches (approx. 18 cm)
- Height: 3-5 inches

**Aspect ratio**: Typically 4:3 or 16:9

### Resolution

**Vector figures**: No need to consider resolution

**Raster figures**:
- Minimum: 300 DPI
- Recommended: 600 DPI
- High quality: 1200 DPI

## Common Errors

### Error 1: Using Raster Format

Not recommended: Saving as PNG/JPG
Recommended: Saving as PDF/EPS

### Error 2: Non-Colorblind-Friendly Colors

Not recommended: Red and green combination
Recommended: Use Okabe-Ito color scheme

### Error 3: Missing Error Representation

Not recommended: Showing only mean values
Recommended: Add error bars/bands

### Error 4: Truncated Axes

Not recommended: Y-axis starting at 80% (exaggerates differences)
Recommended: Y-axis starting at 0% (or state the reason)

### Error 5: Overly Complex Figures

Not recommended: One figure with 10+ curves
Recommended: Split into multiple figures or use subplots

### Error 6: Font Too Small

Not recommended: Label font 6 pt
Recommended: Label font 10-12 pt

## Checklist

Before submission, verify:

- [ ] Using vector format (PDF/EPS)
- [ ] Colorblind-friendly colors (Okabe-Ito or Paul Tol)
- [ ] Readable in black and white (tested)
- [ ] Includes error bars/bands
- [ ] Caption states error type
- [ ] Axis labels clear (including units)
- [ ] Legend does not obscure data
- [ ] Font size appropriate (>=8 pt)
- [ ] Line width appropriate (1.5-2.0 pt)
- [ ] Caption is self-contained

## Recommended Tools

**Python**:
- matplotlib: Basic plotting
- seaborn: Statistical visualization
- plotly: Interactive charts

**Color tools**:
- ColorBrewer: Color scheme selection
- Coblis: Colorblindness simulator

**Format conversion**:
- Inkscape: SVG editing and conversion
- Adobe Illustrator: Professional graphics editing

## References

- [Ten Simple Rules for Better Figures](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833)
- [Okabe-Ito Color Palette](https://jfly.uni-koeln.de/color/)
- [Paul Tol's Notes on Colour](https://personal.sron.nl/~pault/)

## Summary

Key points for publication-quality visualization:

1. **Vector format** - PDF/EPS
2. **Colorblind-friendly** - Okabe-Ito colors
3. **Error representation** - Error bars/bands
4. **Clear labeling** - Axes, legend, caption
5. **Readable in black and white** - Test grayscale printing

Following these principles produces clear, accurate, and professional paper figures.
