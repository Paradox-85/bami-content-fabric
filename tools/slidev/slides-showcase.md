---
theme: default
name: BAMi Slidev — Component Showcase
head:
  - - link
    - rel: stylesheet
      href: /styles/bami-tokens.css
---

---
layout: bami-cover
eyebrow: Phase P0 Complete
kicker: BAMI ENGINEERING
hero: BAMi Slidev Components
subtitle: Three Vue components with chromed BAMi layouts
steps: ["TierPricingCards", "PhasedRolloutTimeline", "KpiStrip", "Brand Chrome", "PDF Export"]
---

---
layout: bami-content
title: Pricing — TierPricingCards
---

<TierPricingCards :tiers='[
  {"name":"Basic","price":"1k","features":["Discovery","Report"],"cta":"Start"},
  {"name":"Pro","price":"3k","features":["Discovery","Engineering","Support"],"cta":"Contact Us"},
  {"name":"Enterprise","price":"Custom","features":["Unlimited projects","Dedicated team"],"cta":"Talk to us"}
]' highlight="Pro" currency="€" />

---
layout: bami-content
title: Roadmap — PhasedRolloutTimeline
---

<PhasedRolloutTimeline :periods='[
  {"key":"q1","label":"Q1 2026","weeks":["Jan","Feb","Mar"]},
  {"key":"q2","label":"Q2 2026","weeks":["Apr","May","Jun"]},
  {"key":"q3","label":"Q3 2026","weeks":["Jul","Aug","Sep"]}
]' :phases='[
  {"name":"Discovery","color":"primary","tasks":[
    {"label":"Requirements","bars":[{"period_key":"q1","start":0.0,"duration":0.7}]},
    {"label":"Stakeholder interviews","bars":[{"period_key":"q1","start":0.5,"duration":0.5}]}
  ],"milestone":{"period_key":"q1","position":0.85,"label":"Kickoff","date":"15 Mar 2026"}},
  {"name":"Design","color":"primary_dark","tasks":[
    {"label":"Architecture","bars":[{"period_key":"q1","start":0.6,"duration":0.5}]},
    {"label":"UI/UX","bars":[{"period_key":"q2","start":0.0,"duration":0.6}]}
  ]},
  {"name":"Build","color":"positive","tasks":[
    {"label":"Development","bars":[{"period_key":"q2","start":0.2,"duration":1.0}]},
    {"label":"Testing","bars":[{"period_key":"q3","start":0.0,"duration":0.8}]}
  ],"milestone":{"period_key":"q3","position":0.5,"label":"Release","date":"01 Sep 2026"}}
]' :today='{"at_period_key":"q2","position":0.3}' />

---
layout: bami-content
title: KPI Strip — KpiStrip
---

<KpiStrip :kpis='[
  {"number":"42","label":"Projects delivered","color":"primary","delta":"+12%","period":"YoY"},
  {"number":"99%","label":"Client satisfaction","color":"positive","delta":"+3%","period":"QTD"},
  {"number":"€1.8M","label":"Revenue","color":"primary_dark","delta":"+18%"},
  {"number":"94%","label":"On-time delivery","color":"warning","delta":"-2%","period":"MTD"}
]' />

---
layout: bami-closing
eyebrow: Next Steps
hero: Ready to move forward.
subtitle: The dual-renderer pipeline is operational
step_numbers: ["01", "02", "03"]
step_titles: ["Intermediate JSON", "Markdown Generator", "Vue Components"]
step_bodies: ["Schema + examples", "JSON → Slidev .md", "3 branded components"]
contact: info@bamiengineering.com
---
