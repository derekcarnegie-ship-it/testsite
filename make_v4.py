with open('c:/Users/derek/Desktop/Claudetests/carbon_emissions_gdp_v3.html', 'r', encoding='utf-8') as f:
    html = f.read()

issues = []

def rep(old, new, label, count=1):
    global html
    n = html.count(old)
    if n == 0:
        issues.append(f"NOT FOUND: {label}")
    elif count != -1 and n != count:
        issues.append(f"WARN ({n} found, expected {count}): {label}")
    else:
        print(f"  OK: {label}")
    html = html.replace(old, new)

# ── CSS layout ────────────────────────────────────────────────────────────────
rep(
    '    margin-left: -8px;\n  }',
    '    margin-left: 0;\n  }',
    'eyebrow margin-left: 0'
)
rep(
    '    left: -10px;\n    transform: translateY(-50%);',
    '    left: 0;\n    transform: translateY(-50%);',
    'title-amp CSS left: 0 (JS sets bearing offset)'
)
# CSS opacity transition 1s -> 1.2s (both #highlight-box and #right-desc)
rep(
    '    transition: opacity 1s ease;\n  }',
    '    transition: opacity 1.2s ease;\n  }',
    'CSS opacity 1s->1.2s (both boxes)', count=-1
)
rep(
    '  .website {\n    margin-top: 10px;',
    '  .website {\n    margin-top: 18px;',
    'website margin-top 10->18px'
)

# ── Source note ───────────────────────────────────────────────────────────────
rep(
    'Data are plotted on a log-log scale.<br>Source:',
    'Data are plotted on a log-log scale. Figure includes all countries with available data for 2000&#x2013;23.<br>Source:',
    'add sentence to source notes'
)

# ── fitTitle rewrite ──────────────────────────────────────────────────────────
old_fit = (
    "(function fitTitle() {\n"
    "  const wrap  = document.querySelector('.title-wrap');\n"
    "  const lines = wrap.querySelectorAll('.title-line');\n"
    "  const avail = wrap.offsetWidth;\n"
    "  const em = lines[1];  // 'Emissions' is the longer word\n"
    "  em.style.display    = 'inline-block';\n"
    "  em.style.width      = 'auto';\n"
    "  em.style.whiteSpace = 'nowrap';\n"
    "  let fs = 54;\n"
    "  em.style.fontSize = fs + 'px';\n"
    "  while (em.offsetWidth < avail) { em.style.fontSize = (++fs) + 'px'; }\n"
    "  fs--;  // back off one step so it fits exactly\n"
    "  em.style.display    = '';\n"
    "  em.style.width      = '';\n"
    "  em.style.whiteSpace = '';\n"
    "  em.style.fontSize   = fs + 'px';\n"
    "  lines[0].style.fontSize = fs + 'px';\n"
    "  // Scale the background \"&\" proportionally\n"
    "  const amp = wrap.querySelector('.title-amp');\n"
    "  amp.style.fontSize = Math.round(184 * fs / 54) + 'px';\n"
    "}());"
)
new_fit = (
    "(function fitTitle() {\n"
    "  const wrap  = document.querySelector('.title-wrap');\n"
    "  const lines = wrap.querySelectorAll('.title-line');\n"
    "  const avail = wrap.offsetWidth;\n"
    "  const em = lines[1];  // 'Emissions' is the longer word\n"
    "  em.style.display    = 'inline-block';\n"
    "  em.style.width      = 'auto';\n"
    "  em.style.whiteSpace = 'nowrap';\n"
    "  let fs = 54;\n"
    "  em.style.fontSize = fs + 'px';\n"
    "  while (em.offsetWidth < avail) { em.style.fontSize = (++fs) + 'px'; }\n"
    "  fs--;  // fs = font-size that fills the full panel width\n"
    "  em.style.display    = '';\n"
    "  em.style.width      = '';\n"
    "  em.style.whiteSpace = '';\n"
    "  // Title lines at 90% so the \"&\" stands out above the text\n"
    "  const fsTitle = Math.round(fs * 0.9);\n"
    "  em.style.fontSize       = fsTitle + 'px';\n"
    "  lines[0].style.fontSize = fsTitle + 'px';\n"
    "  // Keep \"&\" at full-width scale\n"
    "  const amp = wrap.querySelector('.title-amp');\n"
    "  const ampFs = Math.round(184 * fs / 54);\n"
    "  amp.style.fontSize = ampFs + 'px';\n"
    "  // Align visible left of \"&\" glyph with content-area left edge\n"
    "  // (~6.5% left side bearing for Helvetica Neue Black \"&\")\n"
    "  amp.style.left = '-' + Math.round(ampFs * 0.065) + 'px';\n"
    "}());"
)
rep(old_fit, new_fit, 'fitTitle: title 90%, & full-width, & left aligned')

# ── JS timing x1.2 ───────────────────────────────────────────────────────────
rep('const PHASE1_MS = 4200;', 'const PHASE1_MS = 5040;', 'PHASE1_MS 4200->5040')
rep('setTimeout(phase1, 300)', 'setTimeout(phase1, 360)', 'phase1 delay 300->360')

rep(
    "setTimeout(() => { el.textContent = txt; el.style.opacity = '1'; }, 600);",
    "setTimeout(() => { el.textContent = txt; el.style.opacity = '1'; }, 720);",
    'desc() delay 600->720'
)
rep(
    "  el.style.transition = 'opacity 1s ease';\n"
    "  el.style.opacity = '0';\n"
    "  setTimeout(() => { el.innerHTML = html; if (html) { el.style.opacity = '1'; } }, 600);",
    "  el.style.transition = 'opacity 1.2s ease';\n"
    "  el.style.opacity = '0';\n"
    "  setTimeout(() => { el.innerHTML = html; if (html) { el.style.opacity = '1'; } }, 720);",
    'highlightFade 1s->1.2s, 600->720'
)

# Phase 1 end
rep(
    "        ph1Tips.selectAll('circle').transition().duration(600)\n"
    "          .attr('fill', C.linesGrey).attr('opacity', 0.3)\n"
    "          .transition().duration(400).attr('opacity', 0);",
    "        ph1Tips.selectAll('circle').transition().duration(720)\n"
    "          .attr('fill', C.linesGrey).attr('opacity', 0.3)\n"
    "          .transition().duration(480).attr('opacity', 0);",
    'phase1 ph1Tips 600->720, 400->480'
)
rep(
    "        paths.transition().duration(800).attr('stroke', C.linesGrey);",
    "        paths.transition().duration(960).attr('stroke', C.linesGrey);",
    'phase1 paths fade 800->960'
)
rep(
    "        setTimeout(phase2, 1000);\n      }, 1000);",
    "        setTimeout(phase2, 1200);\n      }, 1200);",
    'phase1 pause+phase2 delay 1000->1200'
)

# drawTrendPath
rep(
    "    .transition().duration(700).ease(d3.easeLinear)\n    .attr('stroke-dashoffset', 0);",
    "    .transition().duration(840).ease(d3.easeLinear)\n    .attr('stroke-dashoffset', 0);",
    'drawTrendPath line anim 700->840'
)
rep(
    "  lbl_el.transition().delay(600).duration(300).attr('opacity', 1);",
    "  lbl_el.transition().delay(720).duration(360).attr('opacity', 1);",
    'drawTrendPath label delay 600->720, dur 300->360'
)

# Phase 2
rep("    setTimeout(phase3, 2000);", "    setTimeout(phase3, 2400);", 'phase2 setTimeout(phase3) 2000->2400')
rep(
    "  }, 900);\n}\n\n// ------ PHASE 3:",
    "  }, 1080);\n}\n\n// ------ PHASE 3:",
    'phase2 outer timeout 900->1080'
)

# Phase 3
rep(
    "  dots2000g.selectAll('circle').transition().duration(700).attr('opacity', 0.22);",
    "  dots2000g.selectAll('circle').transition().duration(840).attr('opacity', 0.22);",
    'phase3 dots2000g dim 700->840'
)
rep(
    "  trend2000p.transition().duration(700).attr('opacity', 0.28);",
    "  trend2000p.transition().duration(840).attr('opacity', 0.28);",
    'phase3 trend2000p 700->840'
)
rep(
    "  trend2000lbl.transition().duration(700).attr('opacity', 0.28);",
    "  trend2000lbl.transition().duration(840).attr('opacity', 0.28);",
    'phase3 trend2000lbl 700->840'
)
rep(
    "    .attr('r', 3.5).attr('fill', C.dot2023).attr('opacity', 0)\n"
    "    .transition().duration(700).attr('opacity', 1);",
    "    .attr('r', 3.5).attr('fill', C.dot2023).attr('opacity', 0)\n"
    "    .transition().duration(840).attr('opacity', 1);",
    'phase3 dots2023g fade-in 700->840'
)
rep("    setTimeout(phase4, 2500);", "    setTimeout(phase4, 3000);", 'phase3 setTimeout(phase4) 2500->3000')
rep(
    "  }, 900);\n}\n\n// ------ PHASE 4:",
    "  }, 1080);\n}\n\n// ------ PHASE 4:",
    'phase3 outer timeout 900->1080'
)

# Phase 4
rep(
    "  dots2000g.selectAll('circle').transition().duration(500).attr('opacity', 0);\n"
    "  dots2023g.selectAll('circle').transition().duration(500).attr('opacity', 0);\n"
    "  trend2000p.transition().duration(500).attr('opacity', 0);\n"
    "  trend2023p.transition().duration(500).attr('opacity', 0);\n"
    "  trend2000lbl.transition().duration(300).attr('opacity', 0);\n"
    "  trend2023lbl.transition().duration(300).attr('opacity', 0);",
    "  dots2000g.selectAll('circle').transition().duration(600).attr('opacity', 0);\n"
    "  dots2023g.selectAll('circle').transition().duration(600).attr('opacity', 0);\n"
    "  trend2000p.transition().duration(600).attr('opacity', 0);\n"
    "  trend2023p.transition().duration(600).attr('opacity', 0);\n"
    "  trend2000lbl.transition().duration(360).attr('opacity', 0);\n"
    "  trend2023lbl.transition().duration(360).attr('opacity', 0);",
    'phase4 fade-out 500->600, 300->360'
)
rep(
    "    paths.filter(d => !DECOUPLE_SET.has(d.country)).transition().duration(600)\n"
    "      .attr('opacity', C.dimmedOp);",
    "    paths.filter(d => !DECOUPLE_SET.has(d.country)).transition().duration(720)\n"
    "      .attr('opacity', C.dimmedOp);",
    'phase4 non-decouple dim 600->720'
)
rep('}, ANIM_MS + 3000);', '}, ANIM_MS + 3600);', 'phase4 ANIM_MS+3000->+3600')
rep(
    "      phase5();\n    }, ANIM_MS + 3600);\n  }, 600);",
    "      phase5();\n    }, ANIM_MS + 3600);\n  }, 720);",
    'phase4 outer setTimeout 600->720'
)

# Phase 5 HIC lines (2 occurrences)
rep(
    ".attr('stroke', C.dot2023).attr('stroke-width', 2).attr('opacity', 0)\n"
    "    .transition().duration(500).attr('opacity', 0.9);",
    ".attr('stroke', C.dot2023).attr('stroke-width', 2).attr('opacity', 0)\n"
    "    .transition().duration(600).attr('opacity', 0.9);",
    'phase5 HIC lines 500->600', count=-1
)
rep(
    "    .text('HIC average')\n    .transition().duration(500).attr('opacity', 1);",
    "    .text('HIC average')\n    .transition().duration(600).attr('opacity', 1);",
    'phase5 HIC label 500->600'
)

# Phase 5 LIC block (one big replace)
rep(
    "  setTimeout(() => {\n"
    "    licLineL.attr('opacity', 0.9)\n"
    "      .transition().duration(700).ease(d3.easeQuadInOut)\n"
    "      .attr('y1', y_lic).attr('y2', y_lic);\n"
    "    licLineR.attr('opacity', 0.9)\n"
    "      .transition().duration(700).ease(d3.easeQuadInOut)\n"
    "      .attr('y1', y_lic).attr('y2', y_lic);\n"
    "    licLabel.attr('y', y_hic)\n"
    "      .transition().duration(700).ease(d3.easeQuadInOut)\n"
    "      .attr('y', y_lic);\n"
    "    setTimeout(() => {\n"
    "      licLabel.transition().duration(400).attr('opacity', 1);\n"
    "    }, 700);\n"
    "  }, 500);",
    "  setTimeout(() => {\n"
    "    licLineL.attr('opacity', 0.9)\n"
    "      .transition().duration(840).ease(d3.easeQuadInOut)\n"
    "      .attr('y1', y_lic).attr('y2', y_lic);\n"
    "    licLineR.attr('opacity', 0.9)\n"
    "      .transition().duration(840).ease(d3.easeQuadInOut)\n"
    "      .attr('y1', y_lic).attr('y2', y_lic);\n"
    "    licLabel.attr('y', y_hic)\n"
    "      .transition().duration(840).ease(d3.easeQuadInOut)\n"
    "      .attr('y', y_lic);\n"
    "    setTimeout(() => {\n"
    "      licLabel.transition().duration(480).attr('opacity', 1);\n"
    "    }, 840);\n"
    "  }, 600);",
    'phase5 LIC block 700->840, 400->480, 500->600'
)

# Phase 5 loop block
rep(
    "  setTimeout(() => {\n"
    "    if (p5group) p5group.selectAll('*').transition().duration(1200).attr('opacity', 0);\n"
    "    paths.transition().duration(1200).attr('opacity', 0);\n"
    "    // Also fade the text panel elements\n"
    "    const hbox  = document.getElementById('highlight-box');\n"
    "    const rdesc = document.getElementById('right-desc');\n"
    "    hbox.style.transition  = 'opacity 1.2s ease';\n"
    "    hbox.style.opacity     = '0';\n"
    "    rdesc.style.transition = 'opacity 1.2s ease';\n"
    "    rdesc.style.opacity    = '0';\n"
    "    setTimeout(() => {\n"
    "      if (p5group) { p5group.remove(); p5group = null; }\n"
    "      startAnimation();\n"
    "    }, 1200);\n"
    "  }, 4500);",
    "  setTimeout(() => {\n"
    "    if (p5group) p5group.selectAll('*').transition().duration(1440).attr('opacity', 0);\n"
    "    paths.transition().duration(1440).attr('opacity', 0);\n"
    "    // Also fade the text panel elements\n"
    "    const hbox  = document.getElementById('highlight-box');\n"
    "    const rdesc = document.getElementById('right-desc');\n"
    "    hbox.style.transition  = 'opacity 1.44s ease';\n"
    "    hbox.style.opacity     = '0';\n"
    "    rdesc.style.transition = 'opacity 1.44s ease';\n"
    "    rdesc.style.opacity    = '0';\n"
    "    setTimeout(() => {\n"
    "      if (p5group) { p5group.remove(); p5group = null; }\n"
    "      startAnimation();\n"
    "    }, 1440);\n"
    "  }, 5400);",
    'phase5 loop 1200->1440, 4500->5400, 1.2s->1.44s'
)

rep('setTimeout(startAnimation, 600);', 'setTimeout(startAnimation, 720);', 'kick-off 600->720')

# ── write output ─────────────────────────────────────────────────────────────
with open('c:/Users/derek/Desktop/Claudetests/carbon_emissions_gdp_v4.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("\nISSUES:" if issues else "\nNo issues.")
for i in issues:
    print(" ", i)
print("Done.")
