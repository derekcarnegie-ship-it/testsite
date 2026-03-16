#!/usr/bin/env python3
"""
Process WDI emissions/GDP Excel data and generate animated D3.js visualization.
"""
import pandas as pd
import numpy as np
import json
import sys

EXCEL_PATH = r"C:\Users\derek\Desktop\All current files\Data viz practice\WDI - Clean emissions and GDP per capita 2000-23 (10 March 2026).xlsx"
OUTPUT_PATH = r"C:\Users\derek\Desktop\Claudetests\carbon_emissions_gdp_v5.html"

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

  /* ── outer frame (16:9 landscape 1280 × 720) ── */
  #page {
    display: flex;
    width: 1280px;
    height: 720px;
    background: #f0ede8;
    overflow: hidden;
    box-shadow: 0 4px 32px rgba(0,0,0,0.12);
  }

  /* ── left panel (wide chart) ── */
  #chart-panel {
    width: 960px;
    height: 720px;
    flex-shrink: 0;
  }
  #svg-container {
    width: 960px;
    height: 720px;
  }

  /* ── right panel (text) ── */
  #text-panel {
    width: 320px;
    height: 720px;
    flex-shrink: 0;
    padding: 28px 24px 28px 18px;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .eyebrow {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2.2px;
    text-transform: uppercase;
    color: #5a7fa0;
    margin-bottom: 6px;
    margin-left: 0;
  }

  /* title: "Income" / big faded "&" / "Emissions" */
  .title-wrap {
    position: relative;
    line-height: 1;
    margin-top: 14px;
  }
  .title-line {
    font-size: 42px;
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
    font-size: 140px;
    font-weight: 900;
    color: #2d2926;
    opacity: 0.10;
    /* vertically centred between the two words */
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    line-height: 1;
    z-index: 0;
    pointer-events: none;
    user-select: none;
  }

  /* thin rule separating title from description */
  .title-rule {
    width: 100%;
    height: 2px;
    background: #5a7fa0;
    margin-top: 52px;
    margin-bottom: 0;
    opacity: 0.6;
  }
  /* second rule above source notes */
  .source-rule {
    width: 100%;
    height: 2px;
    background: #5a7fa0;
    margin-bottom: 8px;
    opacity: 0.6;
  }

  /* highlight key-message box */
  #highlight-box {
    margin-top: 14px;
    min-height: 100px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    color: #bfb9b3;
    text-align: right;
    line-height: 1.15;
    font-weight: 900;
    font-family: inherit;
    transition: opacity 1.2s ease;
  }

  /* description block – sits below highlight box */
  #right-desc {
    margin-top: 10px;
    font-size: 19px;
    line-height: 1.2;
    color: #666;
    text-align: justify;
    flex: 1;
    transition: opacity 1.2s ease;
  }

  /* source / notes + website – pinned to bottom of text panel */
  .source-notes {
    font-size: 11px;
    line-height: 1.6;
    color: #bbb;
    text-align: justify;
  }
  .website {
    margin-top: 18px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #5a7fa0;
    text-align: right;
  }
</style>
</head>
<body>
<div id="page">

  <!-- LEFT: wide chart -->
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
    <div id="highlight-box"></div>
    <div id="right-desc"></div>
    <div class="source-rule"></div>
    <div class="source-notes">Note: Emissions exclude land-use change and forestry. World Bank country income groups definitions are from FY26. Data are plotted on a log-log scale. Figure includes all countries with available data for 2000&#x2013;23.<br>Source: EDGAR, World Bank.</div>
    <div class="website">derekcarnegie.com</div>
  </div>

</div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ============================================================
// DATA
// ============================================================
const DATA = DATA_PLACEHOLDER;

const PHASE1_MS = 5040;

const DECOUPLE_SET = new Set([
  'Angola','Australia','Austria','Belgium','Botswana','Cameroon','Canada',
  'Cuba','Cyprus','Czechia','Denmark','Equatorial Guinea','Estonia','Eswatini',
  'Fiji','Finland','France','Gambia, The','Germany','Greece','Guinea-Bissau',
  'Hungary','Iceland','Ireland','Israel','Italy','Jamaica','Japan','Jordan',
  'Lesotho','Luxembourg','Malta','Mauritania','Mexico','Namibia','Netherlands',
  'New Zealand','Nigeria','Norway','Palau','Papua New Guinea','Poland','Portugal',
  'Romania','Seychelles','Singapore','Slovak Republic','Slovenia','Solomon Islands',
  'Somalia','South Africa','Spain','Sweden','Switzerland','Timor-Leste',
  'Ukraine','United Kingdom','United States','Uzbekistan'
]);

// ============================================================
// COLOURS
// ============================================================
const C = {
  bg:          '#f0ede8',
  linesStart:  '#5a7fa0',   // blue (matches 2000 dots)
  linesEnd:    '#c8704e',   // orange (matches 2023 dots)
  linesGrey:   '#c3bfba',   // neutral grey after animation
  linesOp:      0.55,
  lw:           1.5,

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
// DIMENSIONS  –  wide chart (960 × 720)
// ============================================================
const M  = { top: 32, right: 55, bottom: 56, left: 72 };
const W  = 960, H = 720;
const IW = W - M.left - M.right;   // 833
const IH = H - M.top  - M.bottom;  // 632

const X_DOM = [2.25, 5.35];
const Y_DOM = [-0.6, 2.45];

// ============================================================
// SCALES
// ============================================================
const xSc = d3.scaleLinear().domain(X_DOM).range([0, IW]);
const ySc = d3.scaleLinear().domain(Y_DOM).range([IH, 0]);

const xTicks = [
  { v: 2.477, lbl: '300'     },
  { v: 3.0,   lbl: '1,000'   },
  { v: 3.477, lbl: '3,000'   },
  { v: 4.0,   lbl: '10,000'  },
  { v: 4.477, lbl: '30,000'  },
  { v: 5.0,   lbl: '100,000' },
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

// Phase-1 colour gradients (one per country, blue→orange along 2000→2023 trajectory)
DATA.forEach((d, i) => {
  const x0 = xSc(d.gdp[0]),  y0 = ySc(d.emissions[0]);
  const x1 = xSc(d.gdp[23]), y1 = ySc(d.emissions[23]);
  const grad = svgDefs.append('linearGradient')
    .attr('id', `ph1g_${i}`)
    .attr('gradientUnits', 'userSpaceOnUse')
    .attr('x1', x0).attr('y1', y0)
    .attr('x2', x1).attr('y2', y1);
  grad.append('stop').attr('offset', '0%').attr('stop-color', C.linesStart);
  grad.append('stop').attr('offset', '100%').attr('stop-color', C.linesEnd);
  d._ph1GradId = `ph1g_${i}`;
});

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
    .attr('fill', C.axis).attr('font-size', 12)
    .text(t.lbl);
});
{ const t = g.append('text').attr('text-anchor', 'middle')
    .attr('fill', '#888').attr('font-size', 13).attr('font-weight', 700);
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
    .attr('fill', C.axis).attr('font-size', 12)
    .text(t.lbl);
});
{ const t = g.append('text').attr('transform', 'rotate(-90)')
    .attr('text-anchor', 'middle')
    .attr('fill', '#888').attr('font-size', 13).attr('font-weight', 700);
  t.append('tspan').attr('x', -IH / 2).attr('y', -52).text('Emissions per capita');
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
  .attr('fill', C.trend2000).attr('font-size', 17).attr('font-weight', 700);
const trend2023lbl = g.append('text').attr('opacity', 0)
  .attr('fill', C.trend2023).attr('font-size', 17).attr('font-weight', 700);

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

function drawTrendPath(el, xs, ys, lbl_el, lbl_txt, yOffset = 0) {
  const { slope, intercept } = linReg(xs, ys);
  const x1 = Math.min(...xs), x2 = Math.max(...xs);
  const y1 = intercept + slope * x1;
  const y2 = intercept + slope * x2;
  el.attr('d', `M${xSc(x1)},${ySc(y1)} L${xSc(x2)},${ySc(y2)}`);
  const len = el.node().getTotalLength();
  el.attr('stroke-dasharray', `${len} ${len}`)
    .attr('stroke-dashoffset', len).attr('opacity', 1)
    .transition().duration(840).ease(d3.easeLinear)
    .attr('stroke-dashoffset', 0);
  const px = xSc(x2) + 8, py = ySc(y2) + yOffset;
  lbl_el.selectAll('*').remove();
  lbl_el.attr('text-anchor', 'start').attr('opacity', 0);
  lbl_el.append('tspan').attr('x', px).attr('y', py).text(lbl_txt.split(' ')[0]);
  lbl_el.append('tspan').attr('x', px).attr('dy', '1.2em').text('trend');
  lbl_el.transition().delay(720).duration(360).attr('opacity', 1);
}

function desc(txt) {
  const el = document.getElementById('right-desc');
  if (!txt) { el.textContent = ''; el.style.opacity = '0'; return; }
  el.style.opacity = '0';
  setTimeout(() => { el.textContent = txt; el.style.opacity = '1'; }, 720);
}

function highlight(html) {
  const el = document.getElementById('highlight-box');
  el.style.transition = 'none';
  el.innerHTML = html;
  if (html) { el.style.opacity = '1'; }
}

function highlightFade(html) {
  const el = document.getElementById('highlight-box');
  el.style.transition = 'opacity 1.2s ease';
  el.style.opacity = '0';
  setTimeout(() => { el.innerHTML = html; if (html) { el.style.opacity = '1'; } }, 720);
}

// ============================================================
// ANIMATION
// ============================================================
let ticker  = null;
let p5group = null;
let ph1Dots = null;

function reset() {
  if (ticker)  { ticker.stop();   ticker  = null; }
  if (ph1Dots) { ph1Dots.remove(); ph1Dots = null; }
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
  highlight('');
}

function startAnimation() {
  reset();
  setTimeout(phase1, 360);
}

// ------ PHASE 1: draw lines 2000 → 2023 ------
function phase1() {
  desc('Global greenhouse gas emissions per capita increased by 12.2% between 2000 and 2023. Per capita emissions have increased in most countries.');
  paths.attr('opacity', 1)
       .attr('stroke', d => `url(#${d._ph1GradId})`);

  // Static start dots (blue, one per country with valid 2000 data)
  ph1Dots = g.append('g').attr('clip-path', 'url(#chart-clip)');
  const ph1Start = ph1Dots.append('g');
  const ph1Tips  = ph1Dots.append('g');

  DATA.forEach(d => {
    const p0 = d.pts[0];
    if (p0 && p0.g !== null && p0.e !== null) {
      ph1Start.append('circle')
        .attr('cx', xSc(p0.g)).attr('cy', ySc(p0.e))
        .attr('r', 3.5).attr('fill', C.dot2000).attr('opacity', 1);
    }
    ph1Tips.append('circle')
      .datum(d)
      .attr('r', 3.5).attr('opacity', 0);
  });

  const startTs   = performance.now();
  const colorInterp = d3.interpolateRgb(C.linesStart, C.linesEnd);
  let rafId = null, done = false;

  function frame(now) {
    if (done) return;
    const t  = Math.min(23, ((now - startTs) / PHASE1_MS) * 23);
    const yi = Math.floor(t);
    const fr = t - yi;
    const tipColor = colorInterp(t / 23);

    highlight(`<span style="font-size:74px;letter-spacing:-2px">${2000 + yi}</span>`);

    paths.each(function(d) {
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
      d._tip = pts.length > 0 ? pts[pts.length - 1] : null;
      d3.select(this).attr('d', lineGen(pts));
    });

    ph1Tips.selectAll('circle').each(function(d) {
      if (d._tip) {
        d3.select(this)
          .attr('cx', xSc(d._tip.g)).attr('cy', ySc(d._tip.e))
          .attr('fill', tipColor).attr('opacity', 1);
      }
    });

    if (t >= 23) {
      done = true;
      // Keep "2023" in highlight during pause
      // Fade ph1Tips to grey colour then out; keep ph1Start blue dots unchanged
      setTimeout(() => {
        ph1Tips.selectAll('circle').transition().duration(720)
          .attr('fill', C.linesGrey).attr('opacity', 0.3)
          .transition().duration(480).attr('opacity', 0);
        // Cross-fade gradient paths → grey:
        // 1. Switch underlying paths to grey immediately (hidden under overlay)
        paths.attr('stroke', C.linesGrey);
        // 2. Overlay gradient copies that fade out, revealing grey underneath
        const ph1GradOverlay = g.append('g').attr('clip-path', 'url(#chart-clip)').attr('opacity', 1);
        DATA.forEach(d => {
          ph1GradOverlay.append('path')
            .attr('fill', 'none')
            .attr('stroke', `url(#${d._ph1GradId})`)
            .attr('stroke-width', C.lw)
            .attr('stroke-linejoin', 'round')
            .attr('stroke-linecap', 'round')
            .attr('opacity', C.linesOp)
            .attr('d', d.pathData[23]);
        });
        ph1GradOverlay.transition().duration(960).attr('opacity', 0)
          .on('end', () => ph1GradOverlay.remove());
        setTimeout(phase2, 1200);
      }, 1200);
    }
    else { rafId = requestAnimationFrame(frame); }
  }

  ticker = { stop: () => { done = true; if (rafId) cancelAnimationFrame(rafId); } };
  rafId  = requestAnimationFrame(frame);
}

// ------ PHASE 2: 2000 dots + trendline ------
function phase2() {
  desc('On average, emissions have grown slower than GDP. This relative decoupling is partly due to the expanding use of renewables, improved energy efficiency, and structural change.');
  highlightFade('<div style="font-size:34px;letter-spacing:1px;line-height:1.05">RELATIVE<br>DECOUPLING</div>');
  paths.attr('d', d => d.pathData[23]);

  // Place dots2000g immediately (same appearance as ph1Start blue dots)
  const valid = DATA.filter(d => d.gdp[0] !== null && d.emissions[0] !== null);
  dots2000g.selectAll('circle').data(valid).enter().append('circle')
    .attr('cx', d => xSc(d.gdp[0])).attr('cy', d => ySc(d.emissions[0]))
    .attr('r', 3.5).attr('fill', C.dot2000).attr('opacity', 1);

  // Remove ph1Dots seamlessly — dots2000g covers ph1Start; tips already faded
  if (ph1Dots) { ph1Dots.remove(); ph1Dots = null; }

  setTimeout(() => {
    drawTrendPath(trend2000p, valid.map(d => d.gdp[0]), valid.map(d => d.emissions[0]),
                 trend2000lbl, '2000 trend', -24);
    setTimeout(phase3, 2400);
  }, 1080);
}

// ------ PHASE 3: 2023 dots + trendline ------
function phase3() {
  // description stays from phase2

  // Dim 2000 elements to let 2023 stand out
  dots2000g.selectAll('circle').transition().duration(840).attr('opacity', 0.22);
  trend2000p.transition().duration(840).attr('opacity', 0.28);
  trend2000lbl.transition().duration(840).attr('opacity', 0.28);

  const valid = DATA.filter(d => d.gdp[23] !== null && d.emissions[23] !== null);
  dots2023g.selectAll('circle').data(valid).enter().append('circle')
    .attr('cx', d => xSc(d.gdp[23])).attr('cy', d => ySc(d.emissions[23]))
    .attr('r', 3.5).attr('fill', C.dot2023).attr('opacity', 0)
    .transition().duration(840).attr('opacity', 1);

  setTimeout(() => {
    drawTrendPath(trend2023p, valid.map(d => d.gdp[23]), valid.map(d => d.emissions[23]),
                 trend2023lbl, '2023 trend', 4);
    setTimeout(phase4, 3000);
  }, 1080);
}

// ------ PHASE 4: decoupling — flowing colour animation ------
function phase4() {
  const ANIM_MS = PHASE1_MS / 2;  // 2100 ms

  // Fade out all dots and trend elements
  dots2000g.selectAll('circle').transition().duration(600).attr('opacity', 0);
  dots2023g.selectAll('circle').transition().duration(600).attr('opacity', 0);
  trend2000p.transition().duration(600).attr('opacity', 0);
  trend2023p.transition().duration(600).attr('opacity', 0);
  trend2000lbl.transition().duration(360).attr('opacity', 0);
  trend2023lbl.transition().duration(360).attr('opacity', 0);

  setTimeout(() => {
    paths.interrupt()
      .attr('stroke', C.linesGrey)
      .attr('stroke-width', C.lw)
      .attr('opacity', C.linesOp);

    desc('A number of countries have reduced their emissions as their incomes have increased. Absolute decoupling is more common among high-income countries.');
    highlightFade('<div style="font-size:34px;letter-spacing:1px;line-height:1.05">INCOME<span style="display:inline-block;transform:scaleX(2);transform-origin:left center">&#x2B06;</span><br>EMISSIONS<span style="display:inline-block;transform:scaleX(2);transform-origin:left center">&#x2B07;</span></div>');

    // Dim non-decoupling paths (opacity only, no size change)
    paths.filter(d => !DECOUPLE_SET.has(d.country)).transition().duration(720)
      .attr('opacity', C.dimmedOp);

    // Build gradient defs and animated overlay paths for decoupling countries.
    // Overlay paths animate via stroke-dashoffset: colour flows from 2000→2023.
    const overlayGroup = g.append('g').attr('clip-path', 'url(#chart-clip)');
    DATA.forEach((d, i) => {
      if (!DECOUPLE_SET.has(d.country)) return;
      const x0 = xSc(d.gdp[0]),  y0 = ySc(d.emissions[0]);
      const x1 = xSc(d.gdp[23]), y1 = ySc(d.emissions[23]);
      const grad = svgDefs.append('linearGradient')
        .attr('id', `dg_${i}`)
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', x0).attr('y1', y0)
        .attr('x2', x1).attr('y2', y1);
      grad.append('stop').attr('offset', '0%').attr('stop-color', C.dot2000);
      grad.append('stop').attr('offset', '100%').attr('stop-color', C.dot2023);
      const op = overlayGroup.append('path')
        .attr('fill', 'none')
        .attr('stroke', `url(#dg_${i})`)
        .attr('stroke-width', C.lw)
        .attr('stroke-linejoin', 'round')
        .attr('stroke-linecap', 'round')
        .attr('d', d.pathData[23]);
      const len = op.node().getTotalLength();
      op.attr('stroke-dasharray', `${len} ${len}`)
        .attr('stroke-dashoffset', len)
        .transition().duration(ANIM_MS).ease(d3.easeLinear)
        .attr('stroke-dashoffset', 0);
    });

    // After animation + display pause, clean up and go to phase 5
    setTimeout(() => {
      overlayGroup.remove();
      svgDefs.selectAll('[id^="dg_"]').remove();
      paths.interrupt()
        .attr('stroke', C.linesGrey)
        .attr('stroke-width', C.lw)
        .attr('opacity', C.linesOp);
      phase5();
    }, ANIM_MS + 3600);
  }, 720);
}

// ------ PHASE 5: income gap — HIC/LIC average lines (then loop) ------
function phase5() {
  desc('Nevertheless, emissions are much higher in wealthier countries. Emissions per capita in high income economies are 8.7 times that in low income economies.');
  highlightFade('<span style="font-size:74px;letter-spacing:-1px">8.7\u00d7</span>');

  // Paths already grey from end of phase 4; show them at normal opacity
  paths.interrupt()
    .attr('stroke', C.linesGrey)
    .attr('stroke-width', C.lw)
    .attr('opacity', C.linesOp);

  if (!p5group) p5group = g.append('g');
  const p5lines = p5group.append('g').attr('clip-path', 'url(#chart-clip)');
  const p5decor = p5group.append('g');

  const HIC_LOG = Math.log10(12.56);  // ≈ 1.099
  const LIC_LOG = Math.log10(1.44);   // ≈ 0.158
  const y_hic = ySc(HIC_LOG);
  const y_lic = ySc(LIC_LOG);
  const MID = IW / 2;
  const GAP = 50;  // half-width of label gap

  // HIC average — two segments + centered label
  p5lines.append('line')
    .attr('x1', 0).attr('x2', MID - GAP)
    .attr('y1', y_hic).attr('y2', y_hic)
    .attr('stroke', C.dot2023).attr('stroke-width', 2).attr('opacity', 0)
    .transition().duration(600).attr('opacity', 0.9);
  p5lines.append('line')
    .attr('x1', MID + GAP).attr('x2', IW)
    .attr('y1', y_hic).attr('y2', y_hic)
    .attr('stroke', C.dot2023).attr('stroke-width', 2).attr('opacity', 0)
    .transition().duration(600).attr('opacity', 0.9);
  p5decor.append('text')
    .attr('x', MID).attr('y', y_hic)
    .attr('fill', C.dot2023).attr('font-size', 13).attr('font-weight', 700)
    .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle').attr('opacity', 0)
    .text('HIC average')
    .transition().duration(600).attr('opacity', 1);

  // LIC line — starts at y_hic, drops to y_lic after 500ms
  const licLineL = p5lines.append('line')
    .attr('x1', 0).attr('x2', MID - GAP)
    .attr('y1', y_hic).attr('y2', y_hic)
    .attr('stroke', C.dot2023).attr('stroke-width', 2).attr('opacity', 0);
  const licLineR = p5lines.append('line')
    .attr('x1', MID + GAP).attr('x2', IW)
    .attr('y1', y_hic).attr('y2', y_hic)
    .attr('stroke', C.dot2023).attr('stroke-width', 2).attr('opacity', 0);
  const licLabel = p5decor.append('text')
    .attr('x', MID).attr('y', y_hic)
    .attr('fill', C.dot2023).attr('font-size', 13).attr('font-weight', 700)
    .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle').attr('opacity', 0)
    .text('LIC average');

  setTimeout(() => {
    licLineL.attr('opacity', 0.9)
      .transition().duration(840).ease(d3.easeQuadInOut)
      .attr('y1', y_lic).attr('y2', y_lic);
    licLineR.attr('opacity', 0.9)
      .transition().duration(840).ease(d3.easeQuadInOut)
      .attr('y1', y_lic).attr('y2', y_lic);
    licLabel.attr('y', y_hic)
      .transition().duration(840).ease(d3.easeQuadInOut)
      .attr('y', y_lic);
    setTimeout(() => {
      licLabel.transition().duration(480).attr('opacity', 1);
    }, 840);
  }, 600);

  // Loop: fade everything out (+0.5s longer), then restart
  setTimeout(() => {
    if (p5group) p5group.selectAll('*').transition().duration(1440).attr('opacity', 0);
    paths.transition().duration(1440).attr('opacity', 0);
    // Also fade the text panel elements
    const hbox  = document.getElementById('highlight-box');
    const rdesc = document.getElementById('right-desc');
    hbox.style.transition  = 'opacity 1.44s ease';
    hbox.style.opacity     = '0';
    rdesc.style.transition = 'opacity 1.44s ease';
    rdesc.style.opacity    = '0';
    setTimeout(() => {
      if (p5group) { p5group.remove(); p5group = null; }
      startAnimation();
    }, 1440);
  }, 5400);
}

// ============================================================
// TITLE AUTO-FIT  –  scale font-size so EMISSIONS fills panel width
// ============================================================
(function fitTitle() {
  const wrap  = document.querySelector('.title-wrap');
  const lines = wrap.querySelectorAll('.title-line');
  const avail = wrap.offsetWidth;
  const em = lines[1];  // 'Emissions' is the longer word
  em.style.display    = 'inline-block';
  em.style.width      = 'auto';
  em.style.whiteSpace = 'nowrap';
  let fs = 54;
  em.style.fontSize = fs + 'px';
  while (em.offsetWidth < avail) { em.style.fontSize = (++fs) + 'px'; }
  fs--;  // fs = font-size that fills the full panel width
  em.style.display    = '';
  em.style.width      = '';
  em.style.whiteSpace = '';
  // Title lines at 90% so the "&" stands out above the text
  const fsTitle = Math.round(fs * 0.9);
  em.style.fontSize       = fsTitle + 'px';
  lines[0].style.fontSize = fsTitle + 'px';
  // Keep "&" at full-width scale
  const amp = wrap.querySelector('.title-amp');
  const ampFs = Math.round(184 * fs / 54);
  amp.style.fontSize = ampFs + 'px';
  // Align visible left of "&" glyph with content-area left edge
  // (~6.5% left side bearing for Helvetica Neue Black "&")
  amp.style.left = '-' + Math.round(ampFs * 0.065) + 'px';
}());

// ============================================================
// KICK OFF
// ============================================================
setTimeout(startAnimation, 720);

// ============================================================
// VIEWPORT FIT  –  scale #page down on small screens
// ============================================================
(function fitPage() {
  function fit() {
    var s = Math.min(1, window.innerWidth / 1280, window.innerHeight / 720);
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
