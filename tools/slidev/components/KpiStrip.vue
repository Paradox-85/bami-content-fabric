<template>
  <div class="bami-kpi-strip">
    <div
      v-for="(kpi, i) in displayKpis"
      :key="i"
      class="bami-kpi-card"
    >
      <div class="bami-kpi-card__number" :style="{ color: kpiColor(kpi) }">
        {{ kpi.number }}
      </div>
      <div class="bami-kpi-card__label">{{ kpi.label }}</div>
      <div v-if="kpi.delta" class="bami-kpi-card__delta" :class="deltaClass(kpi.delta)">
        {{ kpi.delta }}
        <span v-if="kpi.period" class="bami-kpi-card__period">{{ kpi.period }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  kpis:    { type: Array, required: true },
  columns: { type: Number, default: null },
  accent:  { type: String, default: 'primary' },
})

const COLORS = {
  primary:       '#1FB8B8',
  primary_dark:  '#0E7A7A',
  primary_mid:   '#5BD2C7',
  positive:      '#2BAE66',
  negative:      '#C44C4C',
  warning:       '#E0A800',
  neutral:       '#8A8A86',
}

const displayKpis = computed(() => {
  const count = Math.min(props.columns || props.kpis.length, 4)
  return props.kpis.slice(0, count)
})

function kpiColor(kpi) {
  if (kpi.color && COLORS[kpi.color]) return COLORS[kpi.color]
  if (kpi.color) return kpi.color
  return COLORS[props.accent]
}

function deltaClass(delta) {
  if (!delta) return ''
  const str = String(delta)
  if (str.startsWith('+')) return 'bami-kpi-card__delta--positive'
  if (str.startsWith('-')) return 'bami-kpi-card__delta--negative'
  return ''
}
</script>

<style scoped>
.bami-kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
}
.bami-kpi-card {
  padding: 16px;
  background: #FFFFFF;
  border-radius: 6px;
  border: 1px solid #F0F0F0;
  border-top: 4px solid #1FB8B8;
}
.bami-kpi-card__number {
  font-size: 40pt;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 4px;
}
.bami-kpi-card__label {
  font-size: 12pt;
  color: #2B2B2B;
  font-weight: 400;
  margin-bottom: 4px;
}
.bami-kpi-card__delta {
  font-size: 10pt;
  font-weight: 700;
}
.bami-kpi-card__delta--positive { color: #2BAE66; }
.bami-kpi-card__delta--negative { color: #C44C4C; }
.bami-kpi-card__period {
  font-size: 8pt;
  color: #8A8A86;
  font-weight: 400;
  margin-left: 4px;
}
</style>
