<script setup>
defineProps({
  name: { type: String, required: true },
  score: { type: Number, required: true },
  delta: { type: String, default: '' },
  color: { type: String, default: '#3987e5' },
})
</script>

<template>
  <div class="stat">
    <div class="top">
      <span class="dot" :style="{ background: color }" />
      <span class="name">{{ name }}</span>
    </div>
    <div class="score">{{ score }}</div>
    <div class="foot">
      <span class="label">健康指数</span>
      <span class="delta" :class="{ up: !delta.startsWith('-') }">{{ delta }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.top { display: flex; align-items: center; gap: 8px; }
.dot { width: 9px; height: 9px; border-radius: 50%; }
.name { color: var(--text-secondary); font-size: 13px; }
.score {
  font-size: 34px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.foot { display: flex; align-items: center; justify-content: space-between; }
.label { color: var(--muted); font-size: 12px; }
.delta { font-size: 12px; color: var(--muted); }
.delta.up { color: var(--good); }
</style>
