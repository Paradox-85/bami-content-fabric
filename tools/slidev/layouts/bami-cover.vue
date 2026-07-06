<template>
  <div class="bami-cover">
    <div class="bami-cover__bg"></div>
    <div class="bami-cover__overlay"></div>

    <!-- Logo: left 864px, top 9px, width 101px -->
    <div class="bami-cover__logo">
      <img src="/bami-logo-cover.png" alt="BAMI" />
    </div>

    <!-- Eyebrow: left 44px, top 47px -->
    <div v-if="eyebrow" class="bami-cover__eyebrow">{{ eyebrow }}</div>

    <!-- Kicker: left 44px, top 206px -->
    <div v-if="kicker" class="bami-cover__kicker">{{ kicker }}</div>

    <!-- Hero: left 44px, top 233px -->
    <h1 v-if="hero" class="bami-cover__hero">{{ hero }}</h1>

    <!-- Subtitle: left 44px, top 341px -->
    <div v-if="subtitle" class="bami-cover__subtitle">{{ subtitle }}</div>

    <!-- Steps: left 44px, top 470px -->
    <div v-if="steps?.length" class="bami-cover__steps-row">
      <template v-for="(step, i) in steps" :key="i">
        <div class="bami-cover__step">{{ step }}</div>
        <div v-if="i < steps.length - 1" class="bami-cover__step-connector"></div>
      </template>
    </div>

    <div class="bami-cover__footer">
      <span class="bami-cover__footer-left">DELIVERING VALUE</span>
      <span class="bami-cover__footer-right">Proprietary &amp; Confidential</span>
    </div>

    <slot />
  </div>
</template>

<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  kicker:  { type: String, default: '' },
  hero:    { type: String, default: '' },
  subtitle:{ type: String, default: '' },
  steps:   { type: Array, default: () => [] },
})
</script>

<style scoped>
.bami-cover {
  position: relative;
  width: 980px;
  height: 551px;
  overflow: hidden;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
  color: #FFFFFF;
}
.bami-cover__bg {
  position: absolute; inset: 0;
  background: url('/bg-cover.jpeg') no-repeat center center;
  background-size: cover; z-index: 0;
}
.bami-cover__overlay {
  position: absolute; inset: 0;
  background: #0A0A0A; opacity: 0.6; z-index: 1;
}
.bami-cover__logo {
  position: absolute;
  left: 864px; top: 9px;
  z-index: 3;
}
.bami-cover__logo img {
  width: 101px; height: auto;
}
.bami-cover__eyebrow {
  position: absolute;
  left: 44px; top: 47px;
  font-size: 13pt; color: #B7E9E6; font-weight: 400;
  white-space: nowrap;
}
.bami-cover__kicker {
  position: absolute;
  left: 44px; top: 206px;
  font-size: 16pt; color: #1FB8B8; font-weight: 700;
  white-space: nowrap;
}
.bami-cover__hero {
  position: absolute;
  left: 44px; top: 233px;
  font-size: 54pt; font-weight: 700; color: #FFFFFF;
  margin: 0; line-height: 1.1;
  white-space: nowrap;
}
.bami-cover__subtitle {
  position: absolute;
  left: 44px; top: 341px;
  font-size: 19pt; color: #F7F6F2; font-weight: 400;
  white-space: nowrap;
}
.bami-cover__steps-row {
  position: absolute;
  left: 44px; top: 470px;
  display: flex;
  align-items: center;
  z-index: 3;
}
.bami-cover__step {
  background: #FFFFFF;
  border: 1px solid #1FB8B8;
  border-radius: 16px;
  padding: 4px 16px;
  font-size: 13pt; font-weight: 700;
  color: #1A1A1A;
  white-space: nowrap;
}
.bami-cover__step-connector {
  width: 12px;
  height: 0;
  border-top: 1.5pt solid #1FB8B8;
  margin: 0 2px;
}
.bami-cover__footer {
  position: absolute;
  left: 44px; right: 44px;
  top: 522px;
  display: flex; justify-content: space-between;
  z-index: 3;
}
.bami-cover__footer-left {
  font-size: 11pt; color: #B7E9E6; font-weight: 700;
}
.bami-cover__footer-right {
  font-size: 11pt; color: #8A8A86; font-weight: 400;
}
</style>
