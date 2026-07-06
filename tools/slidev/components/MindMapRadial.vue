<template>
  <div class="bami-mindmap">
    <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="bami-mindmap__svg">
      <!-- Branch lines -->
      <line
        v-for="(line, i) in branchLines"
        :key="'l'+i"
        :x1="line.x1" :y1="line.y1" :x2="line.x2" :y2="line.y2"
        :stroke="lineColor" stroke-width="2" stroke-dasharray="4,3"
      />
      <!-- Root node -->
      <rect
        :x="rootRect.x" :y="rootRect.y"
        :width="rootRect.w" :height="rootRect.h" rx="8"
        :fill="`var(--bami-${accent})`"
      />
      <text
        :x="rootRect.x + rootRect.w / 2" :y="rootRect.y + rootRect.h / 2 + 4"
        text-anchor="middle" font-size="13" font-weight="700" fill="#FFFFFF"
      >{{ rootText }}</text>
      <!-- Child nodes -->
      <g v-for="(child, ci) in childNodes" :key="'c'+ci">
        <rect
          :x="child.x" :y="child.y"
          :width="child.w" :height="child.h" rx="4"
          fill="#FFFFFF" stroke="#1FB8B8" stroke-width="1.5"
        />
        <text
          :x="child.x + child.w / 2" :y="child.y + child.h / 2 + 4"
          text-anchor="middle" font-size="10" font-weight="600" fill="#1A1A1A"
        >{{ child.label }}</text>
        <!-- Grandchildren -->
        <line
          v-for="(g, gi) in child.grandchildren"
          :key="'g'+ci+'-'+gi"
          :x1="child.x + child.w" :y1="child.y + child.h / 2"
          :x2="child.x + child.w + 30" :y2="child.y + child.h * 0.2 + gi * 22"
          stroke="#8A8A86" stroke-width="1" stroke-dasharray="2,2"
        />
        <text
          v-for="(g, gi) in child.grandchildren"
          :key="'gt'+ci+'-'+gi"
          :x="child.x + child.w + 34" :y="child.y + child.h * 0.2 + gi * 22 + 4"
          font-size="9" fill="#8A8A86"
        >{{ g.label }}</text>
      </g>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  root: { type: Object, required: true },
  accent: { type: String, default: 'primary' },
})

const rootText = computed(() => props.root?.label || '')

const CHILD_W = 120, CHILD_H = 32, GAP = 12
const ROOT_W = 140, ROOT_H = 40

const rootRect = computed(() => ({
  x: 10, y: 100, w: ROOT_W, h: ROOT_H,
}))

const children = computed(() => props.root?.children || [])

const childNodes = computed(() => {
  const n = children.value.length
  const startY = 60 + (Math.max(n * (CHILD_H + GAP), 200) - n * (CHILD_H + GAP)) / 2
  return children.value.map((child, i) => {
    const x = ROOT_W + 60
    const y = startY + i * (CHILD_H + GAP)
    const gc = (child.children || []).slice(0, 4)
    return {
      label: child.label,
      x, y, w: CHILD_W, h: CHILD_H,
      grandchildren: gc,
    }
  })
})

const branchLines = computed(() => {
  const rc = rootRect.value
  return childNodes.value.map(c => ({
    x1: rc.x + rc.w, y1: rc.y + rc.h / 2,
    x2: c.x, y2: c.y + c.h / 2,
  }))
})

const lineColor = computed(() => `var(--bami-${props.accent})`)

const svgW = computed(() => {
  const maxX = Math.max(...childNodes.value.map(c => c.x + c.w + 34 + 120), 0)
  return Math.max(maxX, 350)
})
const svgH = computed(() => {
  const n = Math.max(children.value.length, 1)
  return Math.max(n * (CHILD_H + GAP) + 100, 240)
})
</script>

<style scoped>
.bami-mindmap {
  width: 100%;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
}
.bami-mindmap__svg {
  width: 100%;
  height: auto;
  max-height: 350px;
}
</style>
