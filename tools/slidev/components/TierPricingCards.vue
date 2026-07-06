<template>
  <div class="bami-tier-grid">
    <div
      v-for="tier in tiers"
      :key="tier.name"
      class="bami-tier-card"
      :class="{ 'bami-tier-card--highlight': tier.name === highlight }"
    >
      <div v-if="tier.name === highlight" class="bami-tier-card__accent"></div>
      <h3 class="bami-tier-card__name">{{ tier.name }}</h3>
      <p class="bami-tier-card__price">
        <span class="bami-tier-card__currency">{{ currency }}</span>{{ tier.price }}
      </p>
      <ul class="bami-tier-card__features">
        <li v-for="(f, i) in tier.features || []" :key="i">{{ f }}</li>
      </ul>
      <div v-if="tier.cta" class="bami-tier-card__cta">{{ tier.cta }}</div>
      <div v-if="tier.price_note" class="bami-tier-card__price-note">{{ tier.price_note }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tiers:    { type: Array,  required: true },
  highlight:{ type: String, default: null },
  currency: { type: String, default: '€' },
  accent:   { type: String, default: 'primary' },
})
</script>

<style scoped>
.bami-tier-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
}
.bami-tier-card {
  position: relative;
  background: #FFFFFF;
  border: 1px solid #E8E8E8;
  border-radius: 8px;
  padding: 28px 24px;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.bami-tier-card--highlight {
  border: 2px solid #1FB8B8;
  box-shadow: 0 0 0 3px rgba(31, 184, 184, 0.15), 0 6px 24px rgba(31, 184, 184, 0.2);
  transform: scale(1.02);
}
.bami-tier-card--highlight .bami-tier-card__cta {
  background: #1FB8B8;
  color: #FFFFFF;
  font-weight: 700;
}
.bami-tier-card__accent {
  position: absolute; top: 0; left: 0; right: 0; height: 6px;
  background: #1FB8B8;
  border-radius: 8px 8px 0 0;
}
.bami-tier-card__name {
  font-size: 17pt;
  color: #1A1A1A;
  margin: 0 0 8px;
  font-weight: 700;
}
.bami-tier-card__price {
  font-size: 32pt;
  color: #0E7A7A;
  font-weight: 700;
  margin: 0 0 16px;
}
.bami-tier-card__currency {
  font-size: 18pt;
  color: #8A8A86;
  margin-right: 4px;
}
.bami-tier-card__features {
  list-style: none;
  padding: 0;
  margin: 0;
}
.bami-tier-card__features li {
  font-size: 13pt;
  color: #2B2B2B;
  padding: 4px 0;
  border-bottom: 1px solid #F0F0F0;
}
.bami-tier-card__cta {
  margin-top: 16px;
  padding: 10px 16px;
  background: #E8E8E8;
  color: #1A1A1A;
  border-radius: 4px;
  font-weight: 700;
  text-align: center;
  font-size: 13pt;
  cursor: default;
}
.bami-tier-card__price-note {
  margin-top: 4px;
  font-size: 10pt;
  color: #8A8A86;
}
</style>
