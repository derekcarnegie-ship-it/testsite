#!/usr/bin/env python3
"""
Process WDI emissions/GDP Excel data and generate animated D3.js visualization.
"""
import pandas as pd
import numpy as np
import json
import sys

EXCEL_PATH = r"C:\Users\derek\Desktop\All current files\Data viz practice\WDI - Clean emissions and GDP per capita 2000-23 (10 March 2026).xlsx"
OUTPUT_PATH = r"C:\Users\derek\Desktop\Claudetests\carbon_emissions_gdp.html"

# ---------------------------------------------------------------------------
# World Bank FY2025 income group classifications
# (matched to World Bank country naming conventions)
# ---------------------------------------------------------------------------
HIGH_INCOME = {
    'Andorra', 'Antigua and Barbuda', 'Aruba', 'Australia', 'Austria',
    'Bahamas, The', 'Bahrain', 'Barbados', 'Belgium', 'Bermuda',
    'British Virgin Islands', 'Brunei Darussalam', 'Canada', 'Cayman Islands',
    'Channel Islands', 'Chile', 'Croatia', 'Curacao', 'Cyprus',
    'Czech Republic', 'Czechia', 'Denmark', 'Estonia', 'Faroe Islands', 'Finland',
    'France', 'French Polynesia', 'Germany', 'Gibraltar', 'Greece',
    'Greenland', 'Guam', 'Hong Kong SAR, China', 'Hungary', 'Iceland',
    'Ireland', 'Isle of Man', 'Israel', 'Italy', 'Japan', 'Korea, Rep.',
    'Kuwait', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg',
    'Macao SAR, China', 'Malta', 'Monaco', 'Nauru', 'Netherlands',
    'New Caledonia', 'New Zealand', 'Northern Mariana Islands', 'Norway',
    'Oman', 'Palau', 'Panama', 'Poland', 'Portugal', 'Puerto Rico',
    'Qatar', 'Romania', 'San Marino', 'Saudi Arabia', 'Seychelles',
    'Singapore', 'Sint Maarten (Dutch part)', 'Slovak Republic', 'Slovenia',
    'Spain', 'St. Kitts and Nevis', 'St. Martin (French part)',
    'Sweden', 'Switzerland', 'Taiwan, China', 'Trinidad and Tobago',
    'Turks and Caicos Islands', 'United Arab Emirates', 'United Kingdom',
    'United States', 'Uruguay', 'Virgin Islands (U.S.)',
    # FY2025 additions / reclassifications
    'American Samoa', 'Equatorial Guinea',
}

LOW_INCOME = {
    'Afghanistan', 'Burkina Faso', 'Burundi', 'Central African Republic',
    'Chad', 'Congo, Dem. Rep.', 'Eritrea', 'Ethiopia', 'Gambia, The',
    'Guinea-Bissau', 'Korea, Dem. Rep.', 'Liberia', 'Madagascar',
    'Malawi', 'Mali', 'Mozambique', 'Niger', 'Rwanda', 'Sierra Leone',
    'Somalia', 'South Sudan', 'Sudan', 'Syrian Arab Republic', 'Togo',
    'Uganda', 'Yemen, Rep.',
}


def read_data():
    """Read and parse the Excel file."""
    df = pd.read_excel(EXCEL_PATH, header=None, sheet_name='Sheet1')

    emissions, gdp = {}, {}

    # Block 1: emissions (rows 2–172, 0-indexed)
    for i in range(2, 173):
        country = df.iloc[i, 0]
        if pd.notna(country) and isinstance(country, str):
            vals = []
            for j in range(1, 25):
                v = df.iloc[i, j]
                vals.append(float(v) if pd.notna(v) else None)
            emissions[str(country).strip()] = vals

    # Block 2: GDP (rows 177–347, 0-indexed)
    for i in range(177, 348):
        country = df.iloc[i, 0]
        if pd.notna(country) and isinstance(country, str):
            vals = []
            for j in range(1, 25):
                v = df.iloc[i, j]
                vals.append(float(v) if pd.notna(v) else None)
            gdp[str(country).strip()] = vals

    return emissions, gdp


def process_data(emissions, gdp):
    """Combine, filter, classify."""
    countries = []

    for country, em_vals in emissions.items():
        if country not in gdp:
            continue
        gd_vals = gdp[country]

        # Need valid 2000 and 2023 values
        if em_vals[0] is None or em_vals[-1] is None:
            continue
        if gd_vals[0] is None or gd_vals[-1] is None:
            continue

        # Need at least 20 valid paired observations
        valid = sum(1 for e, g in zip(em_vals, gd_vals) if e is not None and g is not None)
        if valid < 18:
            continue

        # Decoupling: GDP up AND emissions down (using log values, threshold 0.03)
        gdp_change = gd_vals[-1] - gd_vals[0]
        em_change = em_vals[-1] - em_vals[0]
        decoupling = (gdp_change > 0.03) and (em_change < -0.03)

        # Income group
        if country in HIGH_INCOME:
            income_group = 'high'
        elif country in LOW_INCOME:
            income_group = 'low'
        else:
            income_group = 'middle'

        countries.append({
            'country': country,
            'gdp': gd_vals,
            'emissions': em_vals,
            'decoupling': decoupling,
            'income_group': income_group,
        })

    return countries


def main():
    print("Reading data…")
    emissions, gdp = read_data()
    print(f"  Emissions: {len(emissions)} countries")
    print(f"  GDP:       {len(gdp)} countries")

    print("Processing…")
    countries = process_data(emissions, gdp)
    print(f"  Valid countries:  {len(countries)}")
    print(f"  Decoupling:       {sum(1 for c in countries if c['decoupling'])}")
    print(f"  High income:      {sum(1 for c in countries if c['income_group'] == 'high')}")
    print(f"  Middle income:    {sum(1 for c in countries if c['income_group'] == 'middle')}")
    print(f"  Low income:       {sum(1 for c in countries if c['income_group'] == 'low')}")

    data_json = json.dumps(countries)
    html = generate_html(data_json)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\nOutput written to: {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# HTML / D3.js generation
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Income &amp; Emissions</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #e8e3dd;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    overflow: hidden;
  }

  /* ── outer frame (golden-ratio landscape 1.619 : 1) ── */
  #page {
    display: flex;
    width: 1100px;
    height: 680px;
    background: #f0ede8;
    overflow: hidden;
    box-shadow: 0 4px 32px rgba(0,0,0,0.12);
  }

  /* ── left panel (square chart) ── */
  #chart-panel {
    width: 680px;
    height: 680px;
    flex-shrink: 0;
  }
  #svg-container {
    width: 680px;
    height: 680px;
  }

  /* ── right panel (text) ── */
  #text-panel {
    width: 420px;
    height: 680px;
    flex-shrink: 0;
    padding: 40px 40px 32px 34px;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .eyebrow {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.2px;
    text-transform: uppercase;
    color: #5a7fa0;
    margin-bottom: 6px;
    margin-left: -8px;
  }

  /* title: "Income" / big faded "&" / "Emissions" */
  .title-wrap {
    position: relative;
    line-height: 1;
  }
  .title-line {
    font-size: 54px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: -2px;
    display: block;
    text-align: right;
    position: relative;
    z-index: 1;
  }
  /* "Income" very slightly greyed */
  .title-wrap span:nth-child(2) { color: #6d6763; }
  /* "Emissions" in greyish blue */
  .title-wrap span:nth-child(3) { color: #5a7fa0; }
  .title-amp {
    position: absolute;
    font-size: 184px;
    font-weight: 900;
    color: #2d2926;
    opacity: 0.10;
    /* vertically centred between the two words */
    top: 50%;
    left: -8px;
    transform: translateY(-50%);
    line-height: 1;
    z-index: 0;
    pointer-events: none;
    user-select: none;
  }

  /* thin rule separating title from description */
  .title-rule {
    width: 36px;
    height: 2px;
    background: #5a7fa0;
    margin-top: 52px;
    margin-bottom: 0;
    opacity: 0.6;
  }

  /* description block – sits in the middle gap */
  #right-desc {
    margin-top: 12px;
    font-size: 34px;
    line-height: 1.45;
    color: #666;
    text-align: justify;
    flex: 1;
  }

  /* source / notes + website – pinned to bottom of text panel */
  .source-notes {
    font-size: 9px;
    line-height: 1.6;
    color: #bbb;
    text-align: right;
  }
  .website {
    margin-top: 6px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #bbb;
    text-align: right;
  }
</style>
</head>
<body>
<div id="page">

  <!-- LEFT: square chart -->
  <div id="chart-panel">
    <div id="svg-container"></div>
  </div>

  <!-- RIGHT: eyebrow · title · description · source · website -->
  <div id="text-panel">
    <div class="eyebrow">171 Countries &nbsp;·&nbsp; 2000–2023</div>
    <div class="title-wrap">
      <span class="title-amp">&amp;</span>
      <span class="title-line">Income</span>
      <span class="title-line">Emissions</span>
    </div>
    <div class="title-rule"></div>
    <div id="right-desc"></div>
    <div class="source-notes">Note: Emissions exclude land-use change and forestry. World Bank country income groups definitions are from FY26. Data are plotted on a log-log scale. Source: EDGAR, World Bank.</div>
    <div class="website">derekcarnegie.com</div>
  </div>

</div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ============================================================
// DATA
// ============================================================
const DATA = DATA_PLACEHOLDER;

// ============================================================
// COLOURS
// ============================================================
const C = {
  bg:          '#f0ede8',
  linesStart:  '#5a7fa0',   // blue (matches 2000 dots)
  linesEnd:    '#c8704e',   // orange (matches 2023 dots)
  linesGrey:   '#c3bfba',   // neutral grey after animation
  linesOp:      0.55,
  lw:           0.75,

  dot2000:     '#5a7fa0',
  dot2023:     '#c8704e',
  trend2000:   '#5a7fa0',
  trend2023:   '#c8704e',

  decoupling:  '#5c9e8a',
  dimmed:      '#ddd8d2',
  dimmedOp:     0.35,

  highIncome:  '#5a7fa0',
  midIncome:   '#aaa098',
  lowIncome:   '#c8704e',

  axis:        '#aaa098',
  grid:        '#e4ddd6',
  yearColor:   '#d4ccc4',
};

// ============================================================
// DIMENSIONS  –  square chart (680 × 680)
// ============================================================
const M  = { top: 32, right: 90, bottom: 56, left: 74 };
const W  = 680, H = 680;
const IW = W - M.left - M.right;   // 516
const IH = H - M.top  - M.bottom;  // 592

const X_DOM = [2.25, 5.35];
const Y_DOM = [-0.6, 2.45];

// ============================================================
// SCALES
// ============================================================
const xSc = d3.scaleLinear().domain(X_DOM).range([0, IW]);
const ySc = d3.scaleLinear().domain(Y_DOM).range([IH, 0]);

const xTicks = [
  { v: 2.477, lbl: '$300'     },
  { v: 3.0,   lbl: '$1,000'   },
  { v: 3.477, lbl: '$3,000'   },
  { v: 4.0,   lbl: '$10,000'  },
  { v: 4.477, lbl: '$30,000'  },
  { v: 5.0,   lbl: '$100,000' },
];
const yTicks = [
  { v: -0.301, lbl: '0.5' },
  { v:  0,     lbl: '1'   },
  { v:  0.301, lbl: '2'   },
  { v:  0.699, lbl: '5'   },
  { v:  1.0,   lbl: '10'  },
  { v:  1.301, lbl: '20'  },
  { v:  1.699, lbl: '50'  },
  { v:  2.0,   lbl: '100' },
  { v:  2.301, lbl: '200' },
];

// ============================================================
// LINE GENERATOR
// ============================================================
const lineGen = d3.line()
  .x(d => xSc(d.g))
  .y(d => ySc(d.e))
  .defined(d => d.g !== null && d.e !== null)
  .curve(d3.curveCatmullRom.alpha(0.5));

// ============================================================
// PRE-PROCESS DATA
// ============================================================
DATA.forEach(d => {
  d.pts = d.gdp.map((g, i) => ({ g, e: d.emissions[i] }));
  d.pathData = [];
  for (let k = 0; k < 24; k++) {
    d.pathData.push(lineGen(d.pts.slice(0, k + 1)));
  }
});

// ============================================================
// BUILD SVG
// ============================================================
const svg = d3.select('#svg-container')
  .append('svg')
  .attr('viewBox', `0 0 ${W} ${H}`)
  .attr('width', '100%')
  .style('display', 'block');

svg.append('rect').attr('width', W).attr('height', H).attr('fill', C.bg);

const g = svg.append('g').attr('transform', `translate(${M.left},${M.top})`);

// clip path (keep defs reference for gradient creation later)
const svgDefs = svg.append('defs');
svgDefs.append('clipPath').attr('id', 'chart-clip')
  .append('rect').attr('x', 0).attr('y', 0).attr('width', IW).attr('height', IH);

// chart border
g.append('rect')
  .attr('x', 0).attr('y', 0).attr('width', IW).attr('height', IH)
  .attr('fill', 'none').attr('stroke', C.grid).attr('stroke-width', 1);

// grid
yTicks.forEach(t => {
  g.append('line')
    .attr('x1', 0).attr('x2', IW)
    .attr('y1', ySc(t.v)).attr('y2', ySc(t.v))
    .attr('stroke', C.grid).attr('stroke-width', 1);
});
xTicks.forEach(t => {
  g.append('line')
    .attr('x1', xSc(t.v)).attr('x2', xSc(t.v))
    .attr('y1', 0).attr('y2', IH)
    .attr('stroke', C.grid).attr('stroke-width', 1);
});

// x axis
g.append('line')
  .attr('x1', 0).attr('x2', IW).attr('y1', IH).attr('y2', IH)
  .attr('stroke', C.axis).attr('stroke-width', 1.5);
xTicks.forEach(t => {
  g.append('line')
    .attr('x1', xSc(t.v)).attr('x2', xSc(t.v))
    .attr('y1', IH).attr('y2', IH + 5).attr('stroke', C.axis);
  g.append('text')
    .attr('x', xSc(t.v)).attr('y', IH + 17)
    .attr('text-anchor', 'middle')
    .attr('fill', C.axis).attr('font-size', 10)
    .text(t.lbl);
});
{ const t = g.append('text').attr('text-anchor', 'middle')
    .attr('fill', '#888').attr('font-size', 11).attr('font-weight', 700);
  t.append('tspan').attr('x', IW / 2).attr('y', IH + 32).text('GDP per capita');
  t.append('tspan').attr('x', IW / 2).attr('dy', '1.3em').text('2015 USD'); }

// y axis
g.append('line')
  .attr('x1', 0).attr('x2', 0).attr('y1', 0).attr('y2', IH)
  .attr('stroke', C.axis).attr('stroke-width', 1.5);
yTicks.forEach(t => {
  g.append('line')
    .attr('x1', -5).attr('x2', 0)
    .attr('y1', ySc(t.v)).attr('y2', ySc(t.v)).attr('stroke', C.axis);
  g.append('text')
    .attr('x', -9).attr('y', ySc(t.v) + 4)
    .attr('text-anchor', 'end')
    .attr('fill', C.axis).attr('font-size', 10)
    .text(t.lbl);
});
{ const t = g.append('text').attr('transform', 'rotate(-90)')
    .attr('text-anchor', 'middle')
    .attr('fill', '#888').attr('font-size', 11).attr('font-weight', 700);
  t.append('tspan').attr('x', -IH / 2).attr('y', -63).text('Emissions per capita');
  t.append('tspan').attr('x', -IH / 2).attr('dy', '1.3em').text('Tonnes CO\u2082e'); }


// ============================================================
// COUNTRY PATHS
// ============================================================
const pathGroup = g.append('g').attr('class', 'paths').attr('clip-path', 'url(#chart-clip)');

const paths = pathGroup.selectAll('.cp')
  .data(DATA)
  .enter().append('path')
  .attr('class', 'cp')
  .attr('fill', 'none')
  .attr('stroke', C.linesStart)
  .attr('stroke-width', C.lw)
  .attr('stroke-linejoin', 'round')
  .attr('stroke-linecap', 'round')
  .attr('opacity', 0)
  .attr('d', d => d.pathData[0]);

// ============================================================
// YEAR WATERMARK
// ============================================================
const yearLabel = g.append('text')
  .attr('x', IW - 8).attr('y', IH - 10)
  .attr('text-anchor', 'end')
  .attr('fill', C.yearColor)
  .attr('font-size', 62).attr('font-weight', 900)
  .attr('opacity', 0)
  .text('2000');

// ============================================================
// DOT / TRENDLINE LAYERS
// ============================================================
const dots2000g = g.append('g').attr('clip-path', 'url(#chart-clip)');
const dots2023g = g.append('g').attr('clip-path', 'url(#chart-clip)');

const trend2000p = g.append('path')
  .attr('fill', 'none').attr('stroke', C.trend2000)
  .attr('stroke-width', 2.2).attr('stroke-dasharray', '7,4').attr('opacity', 0);
const trend2023p = g.append('path')
  .attr('fill', 'none').attr('stroke', C.trend2023)
  .attr('stroke-width', 2.2).attr('stroke-dasharray', '7,4').attr('opacity', 0);

const trend2000lbl = g.append('text').attr('opacity', 0)
  .attr('fill', C.trend2000).attr('font-size', 14).attr('font-weight', 700);
const trend2023lbl = g.append('text').attr('opacity', 0)
  .attr('fill', C.trend2023).attr('font-size', 14).attr('font-weight', 700);

// ============================================================
// HELPERS
// ============================================================
function linReg(xs, ys) {
  const n = xs.length;
  const sx  = xs.reduce((a, b) => a + b, 0);
  const sy  = ys.reduce((a, b) => a + b, 0);
  const sxy = xs.reduce((s, x, i) => s + x * ys[i], 0);
  const sx2 = xs.reduce((s, x) => s + x * x, 0);
  const slope     = (n * sxy - sx * sy) / (n * sx2 - sx * sx);
  const intercept = (sy - slope * sx) / n;
  return { slope, intercept };
}

function drawTrendPath(el, xs, ys, lbl_el, lbl_txt) {
  const { slope, intercept } = linReg(xs, ys);
  const x1 = Math.min(...xs), x2 = Math.max(...xs);
  const y1 = intercept + slope * x1;
  const y2 = intercept + slope * x2;
  el.attr('d', `M${xSc(x1)},${ySc(y1)} L${xSc(x2)},${ySc(y2)}`);
  const len = el.node().getTotalLength();
  el.attr('stroke-dasharray', `${len} ${len}`)
    .attr('stroke-dashoffset', len).attr('opacity', 1)
    .transition().duration(700).ease(d3.easeLinear)
    .attr('stroke-dashoffset', 0);
  lbl_el
    .attr('x', xSc(x2) - 6).attr('y', ySc(y2) - 6)
    .attr('text-anchor', 'end').text(lbl_txt)
    .attr('opacity', 0).transition().delay(600).duration(300).attr('opacity', 1);
}

function desc(txt) {
  document.getElementById('right-desc').textContent = txt;
}

// ============================================================
// ANIMATION
// ============================================================
let ticker  = null;
let p5group = null;

function reset() {
  if (ticker) { ticker.stop(); ticker = null; }
  if (p5group) { p5group.remove(); p5group = null; }
  svgDefs.selectAll('[id^="dg_"]').remove();

  paths
    .interrupt()
    .attr('stroke', C.linesStart).attr('stroke-width', C.lw).attr('opacity', 0)
    .attr('d', d => d.pathData[0]);

  dots2000g.selectAll('*').remove();
  dots2023g.selectAll('*').remove();
  trend2000p.interrupt().attr('opacity', 0).attr('stroke-dashoffset', 0);
  trend2023p.interrupt().attr('opacity', 0).attr('stroke-dashoffset', 0);
  trend2000lbl.interrupt().attr('opacity', 0);
  trend2023lbl.interrupt().attr('opacity', 0);
  yearLabel.interrupt().attr('opacity', 0).text('2000');
  desc('');
}

function startAnimation() {
  reset();
  setTimeout(phase1, 300);
}

// ------ PHASE 1: draw lines 2000 → 2023 ------
function phase1() {
  desc('Tracing each country\u2019s path from 2000 to 2023\u2026');
  paths.attr('opacity', C.linesOp);
  yearLabel.attr('opacity', 1);

  const PHASE1_MS = 4200;
  const startTs   = performance.now();
  const colorInterp = d3.interpolateRgb(C.linesStart, C.linesEnd);
  let rafId = null, done = false;

  function frame(now) {
    if (done) return;
    const t  = Math.min(23, ((now - startTs) / PHASE1_MS) * 23);
    const yi = Math.floor(t);
    const fr = t - yi;

    paths.attr('stroke', colorInterp(t / 23));
    paths.attr('d', d => {
      const pts = [];
      for (let k = 0; k <= yi; k++) {
        const p = d.pts[k];
        if (p && p.g !== null && p.e !== null) pts.push(p);
      }
      if (fr > 0 && yi < 23) {
        const p0 = d.pts[yi], p1 = d.pts[yi + 1];
        if (p0 && p1 && p0.g !== null && p1.g !== null && p0.e !== null && p1.e !== null)
          pts.push({ g: p0.g + (p1.g - p0.g) * fr, e: p0.e + (p1.e - p0.e) * fr });
      }
      return lineGen(pts);
    });
    yearLabel.text(2000 + yi);

    if (t >= 23) {
      done = true;
      yearLabel.transition().duration(600).attr('opacity', 0);
      paths.transition().duration(800).attr('stroke', C.linesGrey);
      setTimeout(phase2, 1400);
    }
    else { rafId = requestAnimationFrame(frame); }
  }

  ticker = { stop: () => { done = true; if (rafId) cancelAnimationFrame(rafId); } };
  rafId  = requestAnimationFrame(frame);
}

// ------ PHASE 2: 2000 dots + trendline ------
function phase2() {
  desc('2000 \u2014 where countries started. The trend shows emissions rising with income.');
  paths.attr('d', d => d.pathData[23]);

  const valid = DATA.filter(d => d.gdp[0] !== null && d.emissions[0] !== null);
  dots2000g.selectAll('circle').data(valid).enter().append('circle')
    .attr('cx', d => xSc(d.gdp[0])).attr('cy', d => ySc(d.emissions[0]))
    .attr('r', 3).attr('fill', C.dot2000).attr('opacity', 0)
    .transition().duration(700).attr('opacity', 0.75);

  setTimeout(() => {
    drawTrendPath(trend2000p, valid.map(d => d.gdp[0]), valid.map(d => d.emissions[0]),
                 trend2000lbl, '2000 trend');
    setTimeout(phase3, 2000);
  }, 900);
}

// ------ PHASE 3: 2023 dots + trendline ------
function phase3() {
  desc('2023 \u2014 the trendline has shifted downward: emissions have partly decoupled from income.');

  // Dim 2000 elements to let 2023 stand out
  dots2000g.selectAll('circle').transition().duration(700).attr('opacity', 0.22);
  trend2000p.transition().duration(700).attr('opacity', 0.28);
  trend2000lbl.transition().duration(700).attr('opacity', 0.28);

  const valid = DATA.filter(d => d.gdp[23] !== null && d.emissions[23] !== null);
  dots2023g.selectAll('circle').data(valid).enter().append('circle')
    .attr('cx', d => xSc(d.gdp[23])).attr('cy', d => ySc(d.emissions[23]))
    .attr('r', 3).attr('fill', C.dot2023).attr('opacity', 0)
    .transition().duration(700).attr('opacity', 0.75);

  setTimeout(() => {
    drawTrendPath(trend2023p, valid.map(d => d.gdp[23]), valid.map(d => d.emissions[23]),
                 trend2023lbl, '2023 trend');
    setTimeout(phase4, 2800);
  }, 900);
}

// ------ PHASE 4: decoupling highlight (blue→orange gradient) ------
function phase4() {
  // Fade out all dots and trend elements
  dots2000g.selectAll('circle').transition().duration(500).attr('opacity', 0);
  dots2023g.selectAll('circle').transition().duration(500).attr('opacity', 0);
  trend2000p.transition().duration(500).attr('opacity', 0);
  trend2023p.transition().duration(500).attr('opacity', 0);
  trend2000lbl.transition().duration(300).attr('opacity', 0);
  trend2023lbl.transition().duration(300).attr('opacity', 0);

  setTimeout(() => {
    // Snap all paths to neutral grey immediately
    paths.interrupt()
      .attr('stroke', C.linesGrey)
      .attr('stroke-width', C.lw)
      .attr('opacity', C.linesOp);

    const nDec = DATA.filter(d => d.decoupling).length;
    desc(`Decoupling \u2014 ${nDec} countries where emissions fell even as incomes grew.`);

    // Build a per-path linearGradient for each decoupling country.
    // gradientUnits="userSpaceOnUse" coordinates are in the g-transform space
    // (same space used by the path line generator).
    DATA.forEach((d, i) => {
      if (!d.decoupling) return;
      const x0 = xSc(d.gdp[0]),        y0 = ySc(d.emissions[0]);
      const x1 = xSc(d.gdp[23]),       y1 = ySc(d.emissions[23]);
      const grad = svgDefs.append('linearGradient')
        .attr('id', `dg_${i}`)
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', x0).attr('y1', y0)
        .attr('x2', x1).attr('y2', y1);
      grad.append('stop').attr('offset', '0%').attr('stop-color', C.dot2000);
      grad.append('stop').attr('offset', '100%').attr('stop-color', C.dot2023);
    });

    // Set decoupling stroke to gradient immediately (no D3 colour transition),
    // then animate opacity/width for all paths.
    paths.filter(d => d.decoupling).attr('stroke', (d, i) => `url(#dg_${i})`);
    paths.filter(d => d.decoupling).transition().duration(900)
      .attr('stroke-width', 1.7)
      .attr('opacity', 0.92);
    paths.filter(d => !d.decoupling).transition().duration(900)
      .attr('stroke', C.dimmed)
      .attr('stroke-width', 0.6)
      .attr('opacity', C.dimmedOp);

    // After display time, remove gradients, return all paths to grey, then phase 5
    setTimeout(() => {
      paths.interrupt()
        .attr('stroke', C.linesGrey)
        .attr('stroke-width', C.lw)
        .attr('opacity', C.linesOp);
      svgDefs.selectAll('[id^="dg_"]').remove();
      setTimeout(phase5, 300);
    }, 4200);
  }, 600);
}

// ------ PHASE 5: income gap — orange dots + curly brace + 8.7× (then loop) ------
function phase5() {
  desc('Income gap \u2014 in 2023, high-income countries had 8.7\u00d7 greater per-capita income than low-income countries.');

  // Paths already grey from end of phase 4; show them at normal opacity
  paths.interrupt()
    .attr('stroke', C.linesGrey)
    .attr('stroke-width', C.lw)
    .attr('opacity', C.linesOp * 0.7);

  // Append a fresh group for phase 5 elements (no clip, so brace can bleed into margin)
  if (!p5group) p5group = g.append('g');
  const p5dots  = p5group.append('g').attr('clip-path', 'url(#chart-clip)');
  const p5decor = p5group.append('g');  // unclipped: brace + label

  // Orange dots for high- and low-income countries at 2023
  const valid23hl = DATA.filter(d =>
    d.gdp[23] !== null && d.emissions[23] !== null &&
    (d.income_group === 'high' || d.income_group === 'low'));

  p5dots.selectAll('circle').data(valid23hl).enter().append('circle')
    .attr('cx', d => xSc(d.gdp[23]))
    .attr('cy', d => ySc(d.emissions[23]))
    .attr('r', 3.5)
    .attr('fill', C.dot2023)
    .attr('opacity', 0)
    .transition().duration(700).attr('opacity', 0.88);

  // Compute mean emissions to anchor the brace vertically
  const hiV = DATA.filter(d => d.income_group === 'high' && d.emissions[23] !== null);
  const loV = DATA.filter(d => d.income_group === 'low'  && d.emissions[23] !== null);
  const hiMean = hiV.reduce((s, d) => s + d.emissions[23], 0) / hiV.length;
  const loMean = loV.reduce((s, d) => s + d.emissions[23], 0) / loV.length;

  const y_hi  = ySc(hiMean);          // pixel y of high-income cluster (higher up)
  const y_lo  = ySc(loMean);          // pixel y of low-income cluster (lower down)
  const y_mid = (y_hi + y_lo) / 2;
  const q     = (y_lo - y_hi) / 4;   // cubic-bezier control offset

  // Left-facing curly brace: back at bx_r, tip (leftmost point) at bx_l
  const bx_r = IW + 22;
  const bx_l = IW + 7;
  const bracePath =
    `M${bx_r},${y_hi} ` +
    `C${bx_r},${y_hi + q} ${bx_l},${y_mid - q} ${bx_l},${y_mid} ` +
    `C${bx_l},${y_mid + q} ${bx_r},${y_lo - q} ${bx_r},${y_lo}`;

  p5decor.append('path')
    .attr('d', bracePath)
    .attr('fill', 'none')
    .attr('stroke', C.dot2023)
    .attr('stroke-width', 2.2)
    .attr('stroke-linecap', 'round')
    .attr('opacity', 0)
    .transition().delay(800).duration(600).attr('opacity', 1);

  p5decor.append('text')
    .attr('x', bx_r + 8)
    .attr('y', y_mid + 7)
    .attr('fill', C.dot2023)
    .attr('font-size', 20)
    .attr('font-weight', 900)
    .attr('text-anchor', 'start')
    .attr('opacity', 0)
    .text('8.7\u00d7')
    .transition().delay(1100).duration(600).attr('opacity', 1);

  // Loop: fade everything out then restart
  setTimeout(() => {
    if (p5group) p5group.selectAll('*').transition().duration(700).attr('opacity', 0);
    paths.transition().duration(700).attr('opacity', 0);
    setTimeout(() => {
      if (p5group) { p5group.remove(); p5group = null; }
      startAnimation();
    }, 800);
  }, 5500);
}

// ============================================================
// KICK OFF
// ============================================================
setTimeout(startAnimation, 600);

// ============================================================
// VIEWPORT FIT  –  scale #page down on small screens
// ============================================================
(function fitPage() {
  function fit() {
    var s = Math.min(1, window.innerWidth / 1100, window.innerHeight / 680);
    var el = document.getElementById('page');
    el.style.zoom = s;
  }
  fit();
  window.addEventListener('resize', fit);
}());
</script>
</body>
</html>
"""


def generate_html(data_json: str) -> str:
    return HTML_TEMPLATE.replace('DATA_PLACEHOLDER', data_json)


if __name__ == '__main__':
    main()
