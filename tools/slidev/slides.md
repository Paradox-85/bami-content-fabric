---
theme: default
canvasWidth: 980
aspectRatio: 16/9
themeConfig:
  primary: '#1FB8B8'
  primaryDark: '#0E7A7A'
  primaryMid: '#5BD2C7'
  primaryPale: '#B7E9E6'
  positive: '#2BAE66'
  negative: '#C44C4C'
  warning: '#E0A800'
  dark: '#0A0A0A'
  text2: '#1A1A1A'
  text3: '#2B2B2B'
  light: '#F7F6F2'
  muted: '#8A8A86'
  white: '#FFFFFF'
layout: bami-cover
eyebrow: May 2026  |  Sales proposal — Saipem
kicker: BAMI AGENT FACTORY
hero: Guided agent building in your Copilot tenant.
subtitle: An agile service that takes an agent idea from intake to deployment across complexity tiers, with one Quick Proposal for every request.
steps:
  - "Idea"
  - "Evaluation"
  - "Tier 0–3"
  - "Quick Proposal"
  - "Build"
---

---
layout: bami-content
heading: Pricing
section: OUR OFFERING
subheading: Simple, transparent pricing based on complexity tier.
---

<TierPricingCards :tiers='[{"name":"Basic","price":"1k","features":["Discovery","Report"]},{"name":"Pro","price":"3k","features":["Discovery","Engineering","Support"]},{"name":"Enterprise","price":"Custom","features":["Unlimited","Dedicated team"]}]' highlight="Pro" currency="€" />

---
layout: bami-content
heading: Implementation Roadmap
section: PROJECTION
subheading: Phased rollout across three quarters.
---

<PhasedRolloutTimeline :periods='[{"key":"q1","label":"Q1 2026"},{"key":"q2","label":"Q2 2026"},{"key":"q3","label":"Q3 2026"}]' :phases='[{"name":"Discovery","color":"primary","tasks":[{"label":"Requirements","bars":[{"period_key":"q1","start":0.0,"duration":0.8}]}],"milestone":{"period_key":"q1","position":0.8,"label":"Kickoff","date":"Mar"}},{"name":"Build","color":"primary_dark","tasks":[{"label":"Development","bars":[{"period_key":"q2","start":0.0,"duration":0.9}]}]}]' :today='{"at_period_key":"q2","position":0.3}' />

---
layout: bami-content
heading: Impact
section: RESULTS
subheading: Headline metrics from the engagement.
bodytext: Delivered value across the engagement.
---

<KpiStrip :kpis='[{"number":"32%","label":"Cost reduction","color":"positive"},{"number":"4x","label":"Throughput","color":"primary"}]' />

---
layout: bami-closing
eyebrow: NEXT STEPS
hero: Let's start now.
subtitle: Three steps to begin. No commercial commitment after this workshop.
stepNumbers:
  - "01"
  - "02"
  - "03"
stepTitles:
  - "Discovery & governance"
  - "Intake setup"
  - "First two PoCs"
stepBodies:
  - "2-hour workshop with leads from the three departments to map priorities."
  - "Bami configures the intake form and the evaluation model in your tenant."
  - "Pick two ideas (different tiers), run them end-to-end. Decide from evidence."
contact: Let's talk  •  info@bamiengineering.com  •  bamiengineering.com
---
