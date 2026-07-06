<template>
  <div class="bami-flowchart">
    <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="bami-flowchart__svg">
      <!-- Edges (arrows) -->
      <defs>
        <marker :id="`arrow-${_uid}`" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto" :fill="arrowColor">
          <polygon points="0 0, 10 3.5, 0 7" />
        </marker>
      </defs>
      <line
        v-for="(edge, i) in edgeLines"
        :key="'e'+i"
        :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2"
        :stroke="arrowColor" stroke-width="2"
        :marker-end="`url(#arrow-${_uid})`"
      />
      <text
        v-for="(edge, i) in edgeLines"
        :key="'el'+i"
        :x="(edge.x1 + edge.x2) / 2" :y="(edge.y1 + edge.y2) / 2 - 6"
        text-anchor="middle" font-size="11" :fill="arrowColor"
      >{{ edge.label }}</text>

      <!-- Nodes -->
      <g v-for="(node, i) in nodePositions" :key="'n'+i">
        <template v-if="node.type === 'decision'">
          <polygon
            :points="diamondPoints(node.x, node.y)"
            :fill="node.color || `var(--bami-${accent})`" stroke="#FFFFFF" stroke-width="2"
          />
        </template>
        <template v-else-if="node.type === 'start' || node.type === 'end'">
          <ellipse
            :cx="node.x" :cy="node.y" :rx="node.w/2" :rh="node.h/2"
            :fill="node.type === 'start' ? '#2BAE66' : '#C44C4C'"
            stroke="#FFFFFF" stroke-width="2"
          />
        </template>
        <template v-else>
          <rect
            :x="node.x - node.w/2" :y="node.y - node.h/2"
            :width="node.w" :height="node.h" rx="4"
            :fill="node.color || '#FFFFFF'" stroke="#1FB8B8" stroke-width="1.5"
          />
        </template>
        <text
          :x="node.x" :y="node.y + 4"
          text-anchor="middle" font-size="11" font-weight="600"
          :fill="(node.type === 'start' || node.type === 'end') ? '#FFFFFF' : '#1A1A1A'"
        >{{ node.text }}</text>
      </g>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  nodes: { type: Array, required: true },
  edges: { type: Array, required: true },
  accent: { type: String, default: 'primary' },
})

const _uid = computed(() => Math.random().toString(36).slice(2, 8))

const arrowColor = computed(() => `var(--bami-${props.accent})`)

// Auto-layout nodes if x/y not provided (simple top-down)
const nodePositions = computed(() => {
  const levels = {}
  const inDegree = {}
  props.nodes.forEach(n => { inDegree[n.id] = 0 })
  props.edges.forEach(e => { if (inDegree[e.to] !== undefined) inDegree[e.to]++ })

  // Topological sort for level assignment
  const queue = props.nodes.filter(n => inDegree[n.id] === 0).map(n => n.id)
  let level = 0
  const nodeLevel = {}
  while (queue.length) {
    const batch = [...queue]
    queue.length = 0
    batch.forEach(id => {
      nodeLevel[id] = level
      props.edges.filter(e => e.from === id).forEach(e => {
        inDegree[e.to]--
        if (inDegree[e.to] === 0) queue.push(e.to)
      })
    })
    level++
  }

  const levelCounts = {}
  props.nodes.forEach(n => {
    const l = nodeLevel[n.id] || 0
    if (!levelCounts[l]) levelCounts[l] = 0
    levelCounts[l]++
  })

  const maxLevel = Math.max(...Object.keys(levelCounts).map(Number), 0)
  const SPACING_X = 180, SPACING_Y = 100
  const W = 120, H = 50
  const svgW = (maxLevel + 1) * SPACING_X + 80
  const svgH = Math.max(...Object.values(levelCounts)) * SPACING_Y + 60

  const counts = {}
  return props.nodes.map(n => {
    const l = nodeLevel[n.id] || 0
    counts[l] = (counts[l] || 0) + 1
    const idx = counts[l] - 1
    const total = levelCounts[l]
    const x = 60 + l * SPACING_X + SPACING_X / 2
    const y = 40 + idx * SPACING_Y + (total > 1 ? SPACING_Y / 2 : 0)
    return { ...n, x, y, w: W, h: H }
  })
})

const svgW = computed(() => {
  const maxL = Math.max(...nodePositions.value.map(n => n.x), 0)
  return maxL + 120
})
const svgH = computed(() => {
  const maxY = Math.max(...nodePositions.value.map(n => n.y), 0)
  return maxY + 80
})

const edgeLines = computed(() => {
  const map = {}
  nodePositions.value.forEach(n => { map[n.id] = n })
  return props.edges.map(e => {
    const from = map[e.from], to = map[e.to]
    if (!from || !to) return null
    return {
      x1: from.x + from.w / 2, y1: from.y,
      x2: to.x - to.w / 2, y2: to.y,
      label: e.label || '',
    }
  }).filter(Boolean)
})

function diamondPoints(cx, cy) {
  const r = 25
  return `${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`
}
</script>

<style scoped>
.bami-flowchart {
  width: 100%;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
}
.bami-flowchart__svg {
  width: 100%;
  height: auto;
  max-height: 340px;
}
</style>
