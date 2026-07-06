<template>
  <div class="bami-swimlanes">
    <div v-for="(lane, li) in lanes" :key="li" class="bami-swimlane">
      <div class="bami-swimlane__header" :style="{ background: `var(--bami-${lane.color || accent})` }">
        {{ lane.name }}
      </div>
      <div class="bami-swimlane__steps">
        <div
          v-for="(step, si) in lane.steps || []"
          :key="si"
          class="bami-swimlane__step"
        >
          <div class="bami-swimlane__step-dot" :style="{ background: `var(--bami-${lane.color || accent})` }"></div>
          <div class="bami-swimlane__step-body">
            <div class="bami-swimlane__step-label">{{ step.label }}</div>
            <div v-if="step.detail" class="bami-swimlane__step-detail">{{ step.detail }}</div>
          </div>
          <div v-if="step.duration" class="bami-swimlane__step-duration">{{ step.duration }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  lanes: { type: Array, required: true },
  accent: { type: String, default: 'primary' },
})
</script>

<style scoped>
.bami-swimlanes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
}
.bami-swimlane {
  display: flex;
  border: 1px solid #E8E8E8;
  border-radius: 6px;
  overflow: hidden;
  min-height: 60px;
}
.bami-swimlane__header {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 140px;
  flex-shrink: 0;
  color: #FFFFFF;
  font-weight: 700;
  font-size: 12pt;
  padding: 8px;
  text-align: center;
}
.bami-swimlane__steps {
  display: flex;
  flex: 1;
  padding: 8px 12px;
  gap: 16px;
  background: #FFFFFF;
  overflow-x: auto;
}
.bami-swimlane__step {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 140px;
  max-width: 220px;
}
.bami-swimlane__step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
.bami-swimlane__step-body {
  flex: 1;
}
.bami-swimlane__step-label {
  font-size: 11pt;
  font-weight: 600;
  color: #1A1A1A;
}
.bami-swimlane__step-detail {
  font-size: 9pt;
  color: #8A8A86;
  margin-top: 2px;
}
.bami-swimlane__step-duration {
  font-size: 9pt;
  color: #8A8A86;
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 4px;
}
</style>
