<template>
  <div class="bami-funnel">
    <div
      v-for="(stage, i) in stages"
      :key="i"
      class="bami-funnel__stage"
      :class="{ 'bami-funnel__stage--highlight': stage.highlight }"
      :style="{
        width: (100 - i * (80 / Math.max(stages.length - 1, 1))) + '%',
        background: stage.color ? `var(--bami-${stage.color})` : `var(--bami-${accent})`,
      }"
    >
      <div class="bami-funnel__label">{{ stage.label }}</div>
      <div class="bami-funnel__value">{{ stage.value }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stages: { type: Array, required: true },
  accent: { type: String, default: 'primary' },
})
</script>

<style scoped>
.bami-funnel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
  padding: 8px 0;
}
.bami-funnel__stage {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-radius: 4px;
  color: #FFFFFF;
  font-weight: 700;
  transition: width 0.3s ease;
  min-height: 40px;
}
.bami-funnel__stage--highlight {
  box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4px rgba(31, 184, 184, 0.4);
  transform: scale(1.03);
}
.bami-funnel__label {
  font-size: 13pt;
}
.bami-funnel__value {
  font-size: 16pt;
  opacity: 0.9;
}
</style>
