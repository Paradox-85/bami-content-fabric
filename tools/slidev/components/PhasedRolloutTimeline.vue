<template>
  <div class="bami-gantt">
    <!-- Period header row -->
    <div class="bami-gantt__header-row">
      <div class="bami-gantt__label-cell bami-gantt__header-label">Workstream</div>
      <div
        v-for="p in periods"
        :key="p.key"
        class="bami-gantt__period-group"
      >
        <div class="bami-gantt__header-period">{{ p.label }}</div>
        <!-- Week sub-headers -->
        <div v-if="p.weeks?.length" class="bami-gantt__weeks-row">
          <div
            v-for="(wk, wi) in p.weeks"
            :key="wi"
            class="bami-gantt__week-cell"
            :style="{ width: (100 / p.weeks.length) + '%' }"
          >{{ wk }}</div>
        </div>
      </div>
    </div>

    <!-- Phase rows -->
    <div v-for="(phase, pi) in phases" :key="pi">
      <!-- Phase title bar -->
      <div class="bami-gantt__phase-bar-row">
        <div class="bami-gantt__label-cell">
          <span
            class="bami-gantt__phase-indicator"
            :style="{ background: phaseColor(phase) }"
          ></span>
          <span class="bami-gantt__phase-title" :style="{ color: phaseColor(phase) }">
            {{ phase.name }}
          </span>
        </div>
        <div
          v-for="p in periods"
          :key="p.key"
          class="bami-gantt__period-body"
        >
          <!-- Milestone diamond for this phase at this period -->
          <div
            v-if="phase.milestone && phase.milestone.period_key === p.key"
            class="bami-gantt__milestone-container"
            :style="{ left: pctPos(phase.milestone.position || 0.5), zIndex: 10 }"
          >
            <div
              class="bami-gantt__milestone-diamond"
              :style="{ background: phaseColor(phase) }"
            ></div>
            <span class="bami-gantt__milestone-slug">{{ phase.milestone.label }}</span>
            <span v-if="phase.milestone.date" class="bami-gantt__milestone-date">{{ phase.milestone.date }}</span>
          </div>
        </div>
      </div>

      <!-- Task rows within phase -->
      <div
        v-for="(task, ti) in phase.tasks || []"
        :key="ti"
        class="bami-gantt__task-row"
      >
        <div class="bami-gantt__label-cell">
          <span class="bami-gantt__task-label">{{ task.label }}</span>
        </div>
        <div
          v-for="p in periods"
          :key="p.key"
          class="bami-gantt__period-body"
        >
          <div
            v-for="(bar, bi) in taskBars(task, p.key)"
            :key="bi"
            class="bami-gantt__bar"
            :style="{
              left: pctPos(bar.start || 0),
              width: pctPos(bar.duration || 0.15),
              background: barColor(bar, phase.color || accent),
            }"
          >
            <span v-if="bar.label" class="bami-gantt__bar-text">{{ bar.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Today marker -->
    <div
      v-if="today"
      class="bami-gantt__today-line"
      :style="{ left: todayLeft() }"
    >
      <div class="bami-gantt__today-label">Today</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  periods: { type: Array, required: true },
  phases:  { type: Array, required: true },
  today:   { type: Object, default: null },
  accent:  { type: String, default: 'primary' },
})

const COLORS = {
  primary:       '#1FB8B8',
  primary_dark:  '#0E7A7A',
  primary_mid:   '#5BD2C7',
  positive:      '#2BAE66',
  warning:       '#E0A800',
  negative:      '#C44C4C',
  neutral:       '#8A8A86',
}

function phaseColor(phase) {
  return COLORS[phase.color] || COLORS[props.accent] || '#1FB8B8'
}

function taskBars(task, periodKey) {
  return (task.bars || []).filter(b => b.period_key === periodKey)
}

function pctPos(value) {
  return (value * 100) + '%'
}

function barColor(bar, fallback) {
  if (bar.color) return COLORS[bar.color] || bar.color
  return COLORS[fallback] || fallback || '#1FB8B8'
}

function todayLeft() {
  if (!props.today) return '0'
  const pi = props.periods.findIndex(p => p.key === props.today.at_period_key)
  if (pi === -1) return '0'
  const base = (pi / props.periods.length) * 100
  const offset = (props.today.position || 0.5) * (100 / props.periods.length)
  return (base + offset) + '%'
}
</script>

<style scoped>
.bami-gantt {
  position: relative;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
  width: 100%;
  overflow-x: auto;
  font-size: 11pt;
  color: #1A1A1A;
}

/* Header row */
.bami-gantt__header-row {
  display: flex;
  background: #F7F6F2;
  border-radius: 4px 4px 0 0;
  border-bottom: 2px solid #E0E0E0;
}
.bami-gantt__label-cell {
  width: 160px;
  min-width: 160px;
  flex-shrink: 0;
  padding: 6px 8px;
}
.bami-gantt__header-label {
  color: #8A8A86;
  font-weight: 700;
  font-size: 10pt;
  display: flex;
  align-items: center;
}
.bami-gantt__period-group {
  flex: 1;
  text-align: center;
}
.bami-gantt__header-period {
  padding: 6px 4px;
  font-weight: 700;
  color: #8A8A86;
  font-size: 11pt;
  border-left: 1px solid #E0E0E0;
}
.bami-gantt__weeks-row {
  display: flex;
  border-top: 1px solid #E0E0E0;
}
.bami-gantt__week-cell {
  padding: 2px 0;
  font-size: 9pt;
  color: #8A8A86;
  border-left: 1px solid #E0E0E0;
}

/* Phase bar row */
.bami-gantt__phase-bar-row {
  display: flex;
  border-bottom: 1px solid #F0F0F0;
  background: #FAFAFA;
  min-height: 32px;
}
.bami-gantt__phase-indicator {
  display: inline-block;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  vertical-align: middle;
  margin-right: 6px;
}
.bami-gantt__phase-title {
  font-size: 11pt;
  font-weight: 700;
  vertical-align: middle;
}

/* Task row */
.bami-gantt__task-row {
  display: flex;
  border-bottom: 1px solid #F5F5F5;
  min-height: 28px;
}
.bami-gantt__task-label {
  font-size: 10pt;
  color: #2B2B2B;
}

/* Period body — relative container for bars/milestones */
.bami-gantt__period-body {
  flex: 1;
  position: relative;
  min-height: 28px;
  border-left: 1px solid #F0F0F0;
}

/* Task bars */
.bami-gantt__bar {
  position: absolute;
  top: 4px;
  height: 18px;
  border-radius: 3px;
  z-index: 2;
  display: flex;
  align-items: center;
  padding: 0 4px;
  min-width: 4px;
}
.bami-gantt__bar-text {
  color: #FFFFFF;
  font-size: 9pt;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Milestone container */
.bami-gantt__milestone-container {
  position: absolute;
  top: 6px;
  display: flex;
  align-items: center;
  gap: 3px;
  pointer-events: none;
  white-space: nowrap;
}
.bami-gantt__milestone-diamond {
  width: 12px;
  height: 12px;
  transform: rotate(45deg);
  border-radius: 2px;
  flex-shrink: 0;
}
.bami-gantt__milestone-slug {
  font-size: 8pt;
  font-weight: 700;
  color: #0E7A7A;
}
.bami-gantt__milestone-date {
  font-size: 8pt;
  color: #8A8A86;
}

/* Today marker */
.bami-gantt__today-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(196, 76, 76, 0.4);
  z-index: 5;
  pointer-events: none;
}
.bami-gantt__today-label {
  position: absolute;
  top: -14px;
  left: 4px;
  font-size: 8pt;
  font-weight: 700;
  color: #C44C4C;
  white-space: nowrap;
}
</style>
