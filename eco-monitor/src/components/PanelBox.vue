<script setup>
defineProps({
  title: { type: String, required: true },
  sub: { type: String, default: '' },
})
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <span class="bar" />
      <span class="title">{{ title }}</span>
      <span v-if="sub" class="sub">{{ sub }}</span>
    </div>
    <div class="panel-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--brand), var(--brand-2));
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.sub {
  font-size: 12px;
  color: var(--muted);
  margin-left: auto;
}
.panel-body {
  flex: 1;
  min-height: 0;
}
</style>
