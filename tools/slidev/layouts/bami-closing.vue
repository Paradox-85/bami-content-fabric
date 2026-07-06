<template>
  <div class="bami-closing">
    <div class="bami-closing__bg"></div>
    <div class="bami-closing__overlay"></div>

    <!-- Logo: 864px left, 9px top, 101px wide -->
    <div class="bami-closing__logo">
      <img src="/bami-logo-cover.png" alt="BAMI" />
    </div>

    <!-- Eyebrow: left 44px, top 98px -->
    <div v-if="eyebrow" class="bami-closing__eyebrow">{{ eyebrow }}</div>
    <!-- Hero: left 44px, top 123px, 52pt bold #FFFFFF -->
    <h1 v-if="hero" class="bami-closing__hero">{{ hero }}</h1>
    <!-- Subtitle: left 44px, top 216px, 21pt #F7F6F2 -->
    <div v-if="subtitle" class="bami-closing__subtitle">{{ subtitle }}</div>

    <!-- 3 step cards: white #FFFFFF, 274px wide, at y=5.70 = 279px -->
    <div v-if="stepNumbers?.length" class="bami-closing__steps">
      <div v-for="(num, i) in stepNumbers" :key="i" class="bami-closing__step">
        <div class="bami-closing__step-number">{{ num }}</div>
        <div class="bami-closing__step-title">{{ stepTitles[i] || '' }}</div>
        <div class="bami-closing__step-body">{{ stepBodies[i] || '' }}</div>
      </div>
    </div>

    <!-- Contact bar: #1FB8B8 full-width at top 470px, black text -->
    <div v-if="contact" class="bami-closing__contact-bar">
      {{ contact }}
    </div>

    <!-- Footer: left 44px, top 524px -->
    <div class="bami-closing__footer">
      <span class="bami-closing__footer-left">DELIVERING VALUE</span>
      <span class="bami-closing__footer-right">Proprietary &amp; Confidential</span>
    </div>

    <slot />
  </div>
</template>

<script setup>
defineProps({
  eyebrow:     { type: String, default: '' },
  hero:        { type: String, default: '' },
  subtitle:    { type: String, default: '' },
  stepNumbers: { type: Array,  default: () => [] },
  stepTitles:  { type: Array,  default: () => [] },
  stepBodies:  { type: Array,  default: () => [] },
  contact:     { type: String, default: '' },
})
</script>

<style scoped>
.bami-closing {
  position: relative;
  width: 980px;
  height: 551px;
  overflow: hidden;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
  color: #FFFFFF;
}
.bami-closing__bg {
  position: absolute; inset: 0;
  background: url('/bg-cover.jpeg') no-repeat center center;
  background-size: cover; z-index: 0;
}
.bami-closing__overlay {
  position: absolute; inset: 0;
  background: #0A0A0A; opacity: 0.6; z-index: 1;
}
.bami-closing__logo {
  position: absolute;
  left: 864px; top: 9px;
  z-index: 3;
}
.bami-closing__logo img {
  width: 101px; height: auto;
}

/* Eyebrow: (0.9, 2.0) — 16pt bold #1FB8B8 */
.bami-closing__eyebrow {
  position: absolute;
  left: 44px; top: 98px;
  font-size: 16pt; font-weight: 700; color: #1FB8B8;
  z-index: 3;
}
/* Hero: (0.9, 2.5) — 52pt bold #FFFFFF */
.bami-closing__hero {
  position: absolute;
  left: 44px; top: 123px;
  width: 882px;
  font-size: 52pt; font-weight: 700; color: #FFFFFF;
  margin: 0; line-height: 1.1;
  z-index: 3;
}
/* Subtitle: (0.9, 4.4) — 21pt normal #F7F6F2 */
.bami-closing__subtitle {
  position: absolute;
  left: 44px; top: 216px;
  width: 882px;
  font-size: 21pt; color: #F7F6F2; font-weight: 400;
  z-index: 3;
}

/* 3 step cards at y=5.70 → 279px
   Card size: 5.6x2.7" → 274x132px
   Positions: x=1.10/7.20/13.30 → 54/353/652px
   Using semi-transparent white over dark overlay for visibility */
.bami-closing__steps {
  position: absolute;
  left: 54px; top: 279px;
  display: flex;
  gap: 25px;  /* 6.1" - 5.6" = 0.5" gap... actually (7.20-1.10-5.6)=0.5" = 24.5px */
  z-index: 3;
}
.bami-closing__step {
  width: 274px;  /* 5.6" */
  min-height: 132px;  /* 2.7" */
  background: rgba(255, 255, 255, 0.95);
  border-radius: 4px;
  padding: 12px 20px;
  box-sizing: border-box;
}
.bami-closing__step-number {
  font-size: 36pt; font-weight: 700; color: #1FB8B8;
  line-height: 1;
  margin-bottom: 4px;
}
.bami-closing__step-title {
  font-size: 18pt; font-weight: 700; color: #0A0A0A;
  margin-bottom: 6px;
  line-height: 1.2;
}
.bami-closing__step-body {
  font-size: 13pt; color: #4A4A4A;
  line-height: 1.3;
}

/* Contact bar: #1FB8B8 full-width at y=9.60 → 470px, 0.9"=44px tall, BLACK text */
.bami-closing__contact-bar {
  position: absolute;
  left: 0; top: 470px;
  width: 980px;
  height: 44px;
  background: #1FB8B8;
  display: flex;
  align-items: center;
  padding: 0 44px;
  font-size: 16pt; font-weight: 700; color: #0A0A0A;
  z-index: 3;
}

/* Footer: (0.9, 10.70) → 524px */
.bami-closing__footer {
  position: absolute;
  left: 44px; right: 44px;
  top: 524px;
  display: flex; justify-content: space-between;
  z-index: 3;
}
.bami-closing__footer-left {
  font-size: 11pt; color: #B7E9E6; font-weight: 700;
}
.bami-closing__footer-right {
  font-size: 11pt; color: #8A8A86; font-weight: 400;
}
</style>
