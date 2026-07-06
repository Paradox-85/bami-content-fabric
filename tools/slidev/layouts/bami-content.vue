<template>
  <div class="bami-content">
    <div class="bami-content__bg"></div>

    <!-- Title bar: 421px wide, 47px tall -->
    <div class="bami-content__title-bar">
      <div class="bami-content__title">{{ heading }}</div>
    </div>

    <!-- Logo: left 877px, top 17px, width 74px -->
    <div class="bami-content__logo">
      <img src="/bami-logo-content.png" alt="BAMI" />
    </div>

    <!-- Body zone -->
    <div class="bami-content__body">
      <div v-if="section" class="bami-content__section-label">{{ section }}</div>
      <div v-if="subheading" class="bami-content__subheading">{{ subheading }}</div>
      <div v-if="bodytext" class="bami-content__bodytext">{{ bodytext }}</div>
      <div class="bami-content__slot" :class="{ 'bami-content__slot--has-header': section || subheading || bodytext }">
        <slot />
      </div>
    </div>

    <!-- Footer divider: left 29px, top 528px -->
    <div class="bami-content__footer-divider"></div>

    <!-- Footer: left 29px, top 532px -->
    <div class="bami-content__footer">
      <span class="bami-content__footer-left">DELIVERING VALUE</span>
      <span class="bami-content__footer-right">Proprietary &amp; Confidential</span>
    </div>
  </div>
</template>

<script setup>

const props = defineProps({
  heading:    { type: String, default: '' },
  section:    { type: String, default: '' },
  subheading: { type: String, default: '' },
  bodytext:   { type: String, default: '' },
})
</script>

<style scoped>
.bami-content {
  position: relative;
  width: 980px;
  height: 551px;
  overflow: hidden;
  font-family: 'Montserrat', 'Calibri', 'Arial', sans-serif;
  background: #FFFFFF;
}
.bami-content__bg {
  position: absolute; inset: 0;
  background: url('/bg-content.jpeg') no-repeat center center;
  background-size: cover; z-index: 0;
}

/* Title bar: 421px wide, 47px tall */
.bami-content__title-bar {
  position: absolute;
  left: 0; top: 0;
  width: 421px;
  height: 47px;
  background: #0A0A0A;
  z-index: 2;
  display: flex;
  align-items: center;
  padding-left: 29px;
}
.bami-content__title {
  flex: 1;
  font-size: 24pt;
  font-weight: 700;
  color: #FFFFFF;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Logo: separate from title bar */
.bami-content__logo {
  position: absolute;
  left: 877px; top: 17px;
  z-index: 3;
}
.bami-content__logo img {
  width: 74px; height: auto;
}

/* Body zone */
.bami-content__body {
  position: absolute;
  left: 29px; top: 52px;
  right: 29px;
  bottom: 29px;
  z-index: 2;
}

.bami-content__section-label {
  font-size: 13pt;
  color: #1FB8B8;
  font-weight: 700;
  margin-bottom: 4px;
  letter-spacing: 0.5px;
}

.bami-content__subheading {
  font-size: 28pt;
  color: #0A0A0A;
  font-weight: 700;
  margin-bottom: 8px;
  line-height: 1.2;
}

.bami-content__bodytext {
  font-size: 16pt;
  color: #2B2B2B;
  margin-bottom: 16px;
  line-height: 1.4;
}

.bami-content__slot {
  /* Slot fills remaining space */
}

/* Footer divider */
.bami-content__footer-divider {
  position: absolute;
  left: 29px; top: 528px;
  width: 922px;
  height: 0;
  border-top: 0.75pt solid #D9D7D1;
  z-index: 2;
}

/* Footer */
.bami-content__footer {
  position: absolute;
  left: 29px; right: 29px;
  top: 532px;
  display: flex;
  justify-content: space-between;
  z-index: 2;
}
.bami-content__footer-left {
  font-size: 9pt; color: #8A8A86; font-weight: 700;
}
.bami-content__footer-right {
  font-size: 9pt; color: #8A8A86;
}
</style>
