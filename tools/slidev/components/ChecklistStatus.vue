<template>
  <div class="bami-checklist" :style="{ '--cols': clampedCols }">
    <div
      v-for="(item, i) in items"
      :key="i"
      class="bami-checklist__item"
      :class="`bami-checklist__item--${item.status || 'pending'}`"
    >
      <div class="bami-checklist__icon">
        <span v-if="item.status === 'done'">&#10003;</span>
        <span v-else-if="item.status === 'in_progress'">&#9679;</span>
        <span v-else-if="item.status === 'blocked'">&#10007;</span>
        <span v-else>&#9675;</span>
      </div>
      <div class="bami-checklist__body">
        <div class="bami-checklist__label">{{ item.label }}</div>
        <div v-if="item.assignee" class="bami-checklist__assignee">{{ item.assignee }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, required: true },
  columns: { type: Number, default: 1 },
})

const clampedCols = computed(() => Math.max(1, Math.min(props.columns || 1, 2)))
</script>

<style scoped>
.bami-checklist {
  display: grid;
  grid-template-columns: repeat(var(--cols), 1fr);
  gap: 8px;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
}
.bami-checklist__item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid #E8E8E8;
  background: #FFFFFF;
}
.bami-checklist__item--done {
  border-left: 3px solid #2BAE66;
}
.bami-checklist__item--in_progress {
  border-left: 3px solid #1FB8B8;
}
.bami-checklist__item--blocked {
  border-left: 3px solid #C44C4C;
  opacity: 0.7;
}
.bami-checklist__item--pending {
  border-left: 3px solid #8A8A86;
}
.bami-checklist__icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14pt;
  font-weight: 700;
}
.bami-checklist__item--done .bami-checklist__icon { color: #2BAE66; }
.bami-checklist__item--in_progress .bami-checklist__icon { color: #1FB8B8; }
.bami-checklist__item--blocked .bami-checklist__icon { color: #C44C4C; }
.bami-checklist__item--pending .bami-checklist__icon { color: #8A8A86; }
.bami-checklist__label {
  font-size: 11pt;
  font-weight: 600;
  color: #1A1A1A;
}
.bami-checklist__assignee {
  font-size: 9pt;
  color: #8A8A86;
  margin-top: 2px;
}
</style>
