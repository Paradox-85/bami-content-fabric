---
theme: default
head:
  - - link
    - rel: stylesheet
      href: /styles/bami-tokens.css
---
layout: bami-cover
hero: Pipeline Demo
subtitle: All three components
---

---
layout: bami-content
title: Pricing
---

<TierPricingCards :tiers='[{"name":"Basic","price":"1k","features":["Discovery","Report"]},{"name":"Pro","price":"3k","features":["Discovery","Engineering","Support"]},{"name":"Enterprise","price":"Custom","features":["Unlimited","Dedicated team"]}]' highlight="Pro" currency="€" />

---
layout: bami-content
title: Implementation Roadmap
---

<PhasedRolloutTimeline :periods='[{"key":"q1","label":"Q1 2026"},{"key":"q2","label":"Q2 2026"},{"key":"q3","label":"Q3 2026"}]' :phases='[{"name":"Discovery","color":"primary","tasks":[{"label":"Requirements","bars":[{"period_key":"q1","start":0.0,"duration":0.8}]}],"milestone":{"period_key":"q1","position":0.8,"label":"Kickoff","date":"Mar"}},{"name":"Build","color":"primary_dark","tasks":[{"label":"Development","bars":[{"period_key":"q2","start":0.0,"duration":0.9}]}]}]' :today='{"at_period_key":"q2","position":0.3}' />

---
layout: bami-content
title: Impact
---

## Headline metrics
Delivered value across the engagement:

<KpiStrip :kpis='[{"number":"32%","label":"Cost reduction","color":"positive"},{"number":"4x","label":"Throughput","color":"primary"}]' />

---
layout: bami-closing
hero: Let's start.
---
