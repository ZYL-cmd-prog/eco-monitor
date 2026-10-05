<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const navs = [
  { path: '/dashboard', name: '综合大屏', icon: '◈' },
  { path: '/indicators', name: '指标管理', icon: '▤' },
  { path: '/analysis', name: '智能分析', icon: '◬' },
  { path: '/alerts', name: '预警中心', icon: '⚠' },
]

const now = ref('')
let timer = null
function tick() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  now.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}
onMounted(() => { tick(); timer = setInterval(tick, 1000) })
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-mark">绿</div>
        <div class="logo-text">
          <div class="t1">生态环境监测</div>
          <div class="t2">智能分析平台</div>
        </div>
      </div>
      <nav class="nav">
        <router-link v-for="n in navs" :key="n.path" :to="n.path" class="nav-item" active-class="active">
          <span class="icon">{{ n.icon }}</span>
          <span>{{ n.name }}</span>
        </router-link>
      </nav>
      <div class="side-foot">空 · 天 · 地 一体化监测</div>
    </aside>

    <div class="main">
      <header class="header">
        <h1 class="title">城乡生态环境数字化监测与智能分析平台</h1>
        <div class="header-right">
          <span class="tag">长江上游示范区</span>
          <span class="clock">{{ now }}</span>
        </div>
      </header>
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout { display: flex; height: 100vh; }
.sidebar {
  width: 210px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 18px 12px;
  gap: 24px;
  flex-shrink: 0;
}
.logo { display: flex; align-items: center; gap: 10px; padding: 0 8px; }
.logo-mark {
  width: 38px; height: 38px; border-radius: 9px;
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  color: #06231a; font-weight: 800; font-size: 18px;
  display: grid; place-items: center;
}
.logo-text .t1 { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.logo-text .t2 { font-size: 12px; color: var(--muted); }
.nav { display: flex; flex-direction: column; gap: 6px; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 14px; border-radius: 8px;
  color: var(--text-secondary); font-size: 14px;
  transition: all .15s;
}
.nav-item:hover { background: var(--surface-2); color: var(--text-primary); }
.nav-item.active { background: rgba(47, 208, 139, 0.12); color: var(--brand); }
.nav-item .icon { width: 18px; text-align: center; }
.side-foot {
  margin-top: auto; text-align: center;
  color: var(--muted); font-size: 12px;
  padding: 10px; border-top: 1px solid var(--border);
}
.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.header {
  height: 56px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; border-bottom: 1px solid var(--border);
  background: var(--surface); flex-shrink: 0;
}
.title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.header-right { display: flex; align-items: center; gap: 14px; }
.tag {
  padding: 4px 12px; border-radius: 20px; font-size: 12px;
  color: var(--brand); border: 1px solid rgba(47, 208, 139, 0.4);
  background: rgba(47, 208, 139, 0.08);
}
.clock { font-size: 13px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.content { flex: 1; overflow: auto; padding: 18px; }
</style>
