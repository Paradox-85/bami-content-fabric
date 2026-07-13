---
theme: default
title: BAMi Slidev — Component Showcase
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
subtitle: 8 Vue components with chromed BAMi layouts
steps: ["TierPricingCards", "PhasedRolloutTimeline", "KpiStrip", "FunnelDiagram", "DecisionTreeFlowchart", "SwimlaneDiagram", "MindMapRadial", "ChecklistStatus", "Brand Chrome", "PDF Export"]
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
layout: bami-content
title: Funnel Pipeline — FunnelDiagram
---

<FunnelDiagram :stages='[
  {"label":"Awareness","value":"5,000","color":"primary","highlight":true},
  {"label":"Interest","value":"1,200","color":"primary_dark"},
  {"label":"Consideration","value":"600","color":"primary_mid"},
  {"label":"Intent","value":"200","color":"positive"},
  {"label":"Evaluation","value":"80","color":"warning"},
  {"label":"Purchase","value":"25","color":"negative"}
]' accent="primary" />

---
layout: bami-content
title: Decision Tree — DecisionTreeFlowchart
---

<DecisionTreeFlowchart :nodes='[
  {"id":"start","text":"Start","type":"start"},
  {"id":"q1","text":"Is budget approved?","type":"decision"},
  {"id":"p1","text":"Proceed to planning","type":"process"},
  {"id":"end1","text":"Delayed","type":"end"},
  {"id":"p2","text":"Re-evaluate scope","type":"process"},
  {"id":"end2","text":"Cancelled","type":"end"}
]' :edges='[
  {"from":"start","to":"q1"},
  {"from":"q1","to":"p1","label":"Yes"},
  {"from":"q1","to":"p2","label":"No"},
  {"from":"p1","to":"end1"},
  {"from":"p2","to":"end2"}
]' accent="primary" />

---
layout: bami-content
title: Swimlane Process — SwimlaneDiagram
---

<SwimlaneDiagram :lanes='[
  {"name":"Sales","color":"primary","steps":[{"label":"Lead generation","duration":"W1"},{"label":"Discovery call","duration":"W2"}]},
  {"name":"Engineering","color":"primary_dark","steps":[{"label":"Requirements analysis","duration":"W2-W3"},{"label":"Architecture design","duration":"W3-W4"}]},
  {"name":"Delivery","color":"positive","steps":[{"label":"Implementation","duration":"W4-W6"},{"label":"QA & Testing","duration":"W6-W7"},{"label":"Deployment","duration":"W7"}]}
]' accent="primary" />

---
layout: bami-content
title: Mind Map — MindMapRadial
---

<MindMapRadial :root='{
  "label":"Product Vision",
  "children":[
    {"label":"User Research","children":[{"label":"Interviews"},{"label":"Surveys"},{"label":"Analytics"}]},
    {"label":"Design","children":[{"label":"UX Flow"},{"label":"Wireframes"},{"label":"Prototypes"}]},
    {"label":"Development","children":[{"label":"Frontend"},{"label":"Backend"},{"label":"Infrastructure"}]}
  ]
}' accent="primary" />

---
layout: bami-content
title: Checklist Status — ChecklistStatus
---

<ChecklistStatus :items='[
  {"label":"Requirements gathered","status":"done"},
  {"label":"UI/UX approved","status":"done","assignee":"Design"},
  {"label":"Backend API built","status":"in_progress","assignee":"Engineering"},
  {"label":"Integration testing","status":"pending","assignee":"QA"},
  {"label":"Security review","status":"blocked","assignee":"Security"},
  {"label":"Production deployment","status":"pending"}
]' :columns="2" />

---
layout: bami-closing
eyebrow: Next Steps
hero: Ready to move forward.
subtitle: The dual-renderer pipeline is operational
stepNumbers: ["01", "02", "03"]
stepTitles: ["Intermediate JSON", "Markdown Generator", "Vue Components"]
stepBodies: ["Schema + examples", "JSON → Slidev .md", "8 branded components"]
contact: info@bamiengineering.com
---
