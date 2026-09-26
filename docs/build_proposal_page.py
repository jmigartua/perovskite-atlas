#!/usr/bin/env python3
"""Render docs/PROPOSAL.md to a single self-contained HTML page in the family design kit.

Usage: python3 docs/build_proposal_page.py [OUT.html]
Requires pandoc. The page uses Google Fonts (Source Serif 4, Source Sans 3, IBM Plex Mono).
"""
import re, subprocess, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "PROPOSAL.md"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "PROPOSAL.html"

body = subprocess.run(
    ["pandoc", str(SRC), "-f", "markdown+pipe_tables+raw_html", "-t", "html5", "--wrap=none", "--no-highlight"],
    check=True, capture_output=True, text=True).stdout

body = re.sub(r'<pre class="mermaid"><code>(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', body, flags=re.S)
body = re.sub(r'<h1 id="perovskite-atlas">.*?</h1>\s*', '', body, count=1, flags=re.S)
body = body.replace('<p><strong>A knowledge base of thirty years', '<p class="lede"><strong>A knowledge base of thirty years', 1)

SWATCH = '''
<div class="swatches" aria-label="Proposed palette">
  <div class="sw"><span style="background:#2f6b5e"></span><b>octa</b><code>#2f6b5e</code><i>primary</i></div>
  <div class="sw"><span style="background:#a8842f"></span><b>gold</b><code>#a8842f</code><i>secondary</i></div>
  <div class="sw"><span style="background:#b03a2e"></span><b>oxy</b><code>#b03a2e</code><i>status</i></div>
  <div class="sw"><span style="background:#1f2422"></span><b>ink</b><code>#1f2422</code><i>text</i></div>
  <div class="sw"><span style="background:#f3f6f4;border:1px solid var(--line)"></span><b>tint</b><code>#f3f6f4</code><i>bands</i></div>
  <div class="sw"><span style="background:#d6ddd9"></span><b>line</b><code>#d6ddd9</code><i>hairlines</i></div>
</div>
'''
body = body.replace('<h3 id="tokens-proposal">8.2 Tokens (proposal)</h3>', '<h3 id="tokens-proposal">8.2 Tokens (proposal)</h3>' + SWATCH, 1)

WORDMARK = '''
<div class="wm-demo">
  <div class="topline-demo"></div>
  <div class="wm-row">
    <span class="wordmark">perovskite<span class="accent"> atlas</span><span class="wordmark-sub">Structures, modes and phase transitions &middot; UPV/EHU</span></span>
    <nav class="site-nav demo"><a>Series</a><a class="current">Materials</a><a>Structures</a><a>Transitions</a><a>Modes</a><a>Plates</a><a>Publications</a><a>Theses</a><a>Data</a></nav>
  </div>
</div>
'''
body = body.replace('<h3 id="wordmark-and-name">8.3 Wordmark and name</h3>', '<h3 id="wordmark-and-name">8.3 Wordmark and name</h3>' + WORDMARK, 1)

toc = [f'<li><a href="#{m.group(1)}">{re.sub("<.*?>", "", m.group(2))}</a></li>' for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', body)]
TOC = '<nav class="contents" aria-label="Contents"><h4>Contents</h4><ol>' + "".join(toc) + '</ol></nav>'

CSS = r'''
:root{
  --ink:#1f2422; --ink-soft:#535b58; --ink-faint:#7f8884;
  --paper:#ffffff; --tint:#f3f6f4; --line:#d6ddd9; --line-soft:#e6ebe8;
  --octa:#2f6b5e; --octa-soft:#4d8a7c; --gold:#a8842f; --oxy:#b03a2e;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif;
  --sans:"Source Sans 3",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace;
  --maxw:1180px; --gutter:clamp(20px,4vw,48px); --measure:72ch;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ink:#e6e9e7; --ink-soft:#b3bab7; --ink-faint:#8a918e;
    --paper:#15191a; --tint:#1c2221; --line:#2f3736; --line-soft:#262d2c;
    --octa:#6fb3a2; --octa-soft:#8cc6b8; --gold:#d3ad5a; --oxy:#e07b6f; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --ink:#e6e9e7; --ink-soft:#b3bab7; --ink-faint:#8a918e;
  --paper:#15191a; --tint:#1c2221; --line:#2f3736; --line-soft:#262d2c;
  --octa:#6fb3a2; --octa-soft:#8cc6b8; --gold:#d3ad5a; --oxy:#e07b6f; color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--octa);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:3px}
a:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
code,pre{font-family:var(--mono)}
code{font-size:0.88em;background:var(--tint);padding:1px 4px;border-radius:2px}
pre{background:var(--tint);border:1px solid var(--line);border-radius:2px;padding:14px 16px;overflow-x:auto;font-size:13.5px;line-height:1.5}
pre code{background:none;padding:0;font-size:inherit}
pre.mermaid{background:var(--paper);border:1px solid var(--line);padding:16px;overflow-x:auto}
.wrap{max-width:var(--maxw);margin:0 auto;padding-left:var(--gutter);padding-right:var(--gutter)}
.topline{height:4px;background:var(--octa)}
.site-head{border-bottom:1px solid var(--line);background:var(--paper)}
.site-head__inner{max-width:var(--maxw);margin:0 auto;padding:18px var(--gutter);display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap}
.wordmark{font-family:var(--serif);font-weight:600;font-size:24px;color:var(--ink);letter-spacing:-0.01em;display:inline-block}
.wordmark .accent{color:var(--octa);font-weight:400}
.wordmark-sub{display:block;font-family:var(--sans);font-size:12.5px;font-weight:400;color:var(--ink-faint);letter-spacing:.02em;margin-top:1px}
.site-nav{display:flex;gap:22px;flex-wrap:wrap;font-size:15px;font-weight:500}
.site-nav a{color:var(--ink-soft)}
.site-nav a.current{color:var(--ink);border-bottom:2px solid var(--gold);padding-bottom:2px}
.doc-meta{font-size:13.5px;color:var(--ink-faint);display:flex;gap:18px;flex-wrap:wrap;margin:0 0 6px;text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.doc-meta b{color:var(--gold)}
.title-block{padding:56px 0 28px;border-bottom:1px solid var(--line)}
.title-block h1{font-family:var(--serif);font-weight:400;font-size:clamp(30px,4vw,46px);line-height:1.15;letter-spacing:-0.015em;margin:0;max-width:22ch;text-wrap:balance}
.title-block h1 strong{font-weight:700}
.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:56px;padding-top:36px}
@media(max-width:900px){.layout{grid-template-columns:1fr;gap:24px}}
.contents{position:sticky;top:24px;align-self:start;font-size:14px}
.contents h4{margin:0 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-faint);font-weight:600}
.contents ol{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
.contents li{margin:0}
.contents a{display:block;padding:5px 0 5px 12px;color:var(--ink-soft);line-height:1.35;border-left:2px solid transparent;margin-left:-1px}
.contents a:hover{color:var(--octa);text-decoration:none;border-left-color:var(--octa)}
@media(max-width:900px){.contents{position:static}.contents ol{columns:2;gap:24px}}
article{min-width:0}
article > p, article > ul, article > ol, article > h2, article > h3, article > h4, article > blockquote{max-width:var(--measure)}
article p.lede{font-family:var(--serif);font-size:21px;line-height:1.45;color:var(--ink);margin:0 0 18px}
article p.lede strong{font-weight:500}
article h2{font-family:var(--serif);font-weight:600;font-size:28px;letter-spacing:-0.01em;line-height:1.2;margin:56px 0 14px;padding-top:22px;border-top:1px solid var(--line);text-wrap:balance}
article h3{font-family:var(--serif);font-weight:600;font-size:20px;margin:34px 0 10px;text-wrap:balance}
article h4{font-family:var(--sans);font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-faint);margin:26px 0 8px;font-weight:600}
article p{margin:0 0 14px}
article ul,article ol{padding-left:22px;margin:0 0 16px}
article li{margin-bottom:6px}
article strong{font-weight:600}
article hr{display:none}
article sub{font-size:.72em;line-height:0}
.tbl{overflow-x:auto;margin:14px 0 24px;border-top:1px solid var(--line)}
table{border-collapse:collapse;width:100%;font-size:14.5px;line-height:1.45;font-variant-numeric:tabular-nums}
th,td{text-align:left;vertical-align:top;padding:8px 12px 8px 0;border-bottom:1px solid var(--line-soft)}
th{font-family:var(--sans);font-size:12.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-faint);font-weight:600;border-bottom:1px solid var(--line)}
td code{white-space:nowrap}
tbody tr:hover td{background:var(--tint)}
.swatches{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:8px 0 22px;max-width:var(--maxw)}
.sw{display:grid;grid-template-columns:44px 1fr;grid-template-rows:auto auto auto;column-gap:10px;align-items:center;font-size:13px;padding:8px 0;border-top:1px solid var(--line)}
.sw span{grid-row:1/4;width:44px;height:44px;border-radius:2px;display:block}
.sw b{font-family:var(--mono);font-weight:500;color:var(--ink)}
.sw code{background:none;padding:0;color:var(--ink-soft);font-size:12px}
.sw i{font-style:normal;color:var(--ink-faint);font-size:12px}
.wm-demo{border:1px solid var(--line);margin:8px 0 22px;background:var(--paper)}
.topline-demo{height:4px;background:var(--octa)}
.wm-row{padding:16px 20px;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap}
.site-nav.demo a{cursor:default}
.site-foot{background:var(--tint);border-top:1px solid var(--line);padding:40px 0 28px;font-size:14px;margin-top:72px;color:var(--ink-soft)}
.site-foot__inner{max-width:var(--maxw);margin:0 auto;padding:0 var(--gutter);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
.site-foot .faint{color:var(--ink-faint);font-size:13px}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
html{scroll-behavior:smooth}
'''

body = body.replace('<table>', '<div class="tbl"><table>').replace('</table>', '</table></div>')

html = f'''<title>Perovskite Atlas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;0,8..60,700;1,8..60,400&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
<div class="topline"></div>
<header class="site-head">
  <div class="site-head__inner">
    <a href="#top" class="wordmark">perovskite<span class="accent"> atlas</span>
      <span class="wordmark-sub">Structures, modes and phase transitions &middot; UPV/EHU</span>
    </a>
    <nav class="site-nav">
      <a href="#the-proposal-in-eight-lines">Summary</a>
      <a href="#what-exists-today-and-why-it-does-not-satisfy">Diagnosis</a>
      <a href="#b.-alternatives-considered">Alternatives</a>
      <a href="#the-knowledge-model">Model</a>
      <a href="#ingestion-turning-theses-and-papers-into-data">Ingestion</a>
      <a href="#the-website">Website</a>
      <a href="#roadmap-mid-term-about-eighteen-months">Roadmap</a>
      <a href="#a.-decisions-taken-2026-09-26">Decisions</a>
    </nav>
  </div>
</header>
<main class="wrap" id="top">
  <div class="title-block">
    <p class="doc-meta"><span>Design proposal <b>v2.1</b></span><span>2026-09-26</span><span>Decisions taken · Phase 0 scaffolded</span></p>
    <h1><strong>Perovskite Atlas.</strong> A knowledge base for thirty years of structures, modes and phase transitions.</h1>
  </div>
  <div class="layout">
    {TOC}
    <article>
{body}
    </article>
  </div>
</main>
<footer class="site-foot">
  <div class="site-foot__inner">
    <div>Proposal prepared for J. M. Igartua &middot; Department of Physics, UPV/EHU</div>
    <div class="faint">Source: <code>docs/PROPOSAL.md</code> in the perovskite-atlas repository &middot; sibling of igartua, thermomat and emissivity.org</div>
  </div>
</footer>
'''
OUT.write_text(html)
print(OUT, len(html))
