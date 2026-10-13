<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import PanelBox from '../components/PanelBox.vue'
import { uavDemo } from '../data/mock'

// 无人机巡查数据：rs-pipeline/uav.py 生成的 uav.json（演示样例）；缺失时回退内联演示
const uav = ref(null)
const isReal = ref(false)

onMounted(async () => {
  try {
    const res = await fetch('/data/uav.json', { cache: 'no-store' })
    if (res.ok) {
      const d = await res.json()
      // 仅当 uav.json 为完整新结构（含 route/tasks）时采用；旧版稀疏样例回退内联演示
      if (d && d.route && d.tasks) {
        uav.value = d
        isReal.value = true
        return
      }
    }
  } catch (e) { /* 回退演示 */ }
  uav.value = uavDemo
})

const AXIS = {
  axisLine: { lineStyle: { color: '#383835' } },
  axisLabel: { color: '#898781' },
  splitLine: { lineStyle: { color: '#2c2c2a' } },
}

const levelColor = { '红色': '#d03b3b', '橙色': '#d95926', '黄色': '#fab219', '蓝色': '#3987e5' }
const statusColor = {
  '待执行': '#898781', '执行中': '#3987e5', '已完成': '#2fd08b',
  '处理中': '#d95926', '待处理': '#fab219', '已整改': '#2fd08b', '演示样例': '#fab219',
}

const summary = computed(() => uav.value?.summary || {})
const kpiCards = computed(() => [
  { key: 'flights', label: '本月巡查架次', unit: '架次', value: summary.value.flights },
  { key: 'coverage', label: '覆盖面积', unit: 'km²', value: summary.value.coverage },
  { key: 'findings', label: '发现问题', unit: '处', value: summary.value.findings },
  { key: 'rectified', label: '整改完成', unit: '处', value: summary.value.rectified },
])

const taskCols = computed(() => {
  const order = ['待执行', '执行中', '已完成']
  const tasks = uav.value?.tasks || []
  return order.map((s) => ({ status: s, items: tasks.filter((t) => t.status === s) }))
})

const routeOption = computed(() => {
  const wps = uav.value?.route?.waypoints || []
  if (!wps.length) return {}
  return {
    tooltip: { trigger: 'item', formatter: (p) => `航点 ${p.dataIndex + 1}：${p.value[0]}, ${p.value[1]}` },
    grid: { left: 10, right: 16, top: 16, bottom: 34, containLabel: true },
    xAxis: { type: 'value', scale: true, name: '经度 (°)', nameTextStyle: { color: '#898781' }, ...AXIS },
    yAxis: { type: 'value', scale: true, name: '纬度 (°)', nameTextStyle: { color: '#898781' }, ...AXIS },
    series: [
      { type: 'line', data: wps, showSymbol: false, silent: true,
        lineStyle: { color: '#3987e5', width: 2, type: 'dashed' } },
      { type: 'scatter', data: wps.slice(1, -1), symbolSize: 6, itemStyle: { color: '#2fd08b' } },
      { type: 'scatter', data: [wps[0]], symbolSize: 12, itemStyle: { color: '#fab219' },
        label: { show: true, position: 'bottom', formatter: uav.value?.route?.start || '起降点', color: '#c3c2b7', fontSize: 11 } },
    ],
  }
})

const routeSub = computed(() => {
  const r = uav.value?.route
  if (!r) return '演示航线'
  return `${r.area} · 航线 ${r.lengthKm} km`
})
</script>

<template>
  <div class="uav">
    <div class="banner">
      <span class="badge">演示样例</span>
      <span class="banner-text">无人机巡查模块（「空—天—地」之空层）—— 待接入真实无人机正射影像，当前为模块框架演示，以下任务 / 航线 / 发现均为占位数据</span>
    </div>

    <!-- 统计概览 -->
    <div class="kpis">
      <div v-for="k in kpiCards" :key="k.key" class="kpi">
        <div class="kpi-value">{{ k.value }}<span class="kpi-unit">{{ k.unit }}</span></div>
        <div class="kpi-label">{{ k.label }}</div>
      </div>
    </div>

    <!-- 飞行路线示意 + 巡查任务看板 -->
    <div class="grid">
      <PanelBox title="飞行路线示意" :sub="routeSub" class="span2">
        <BaseChart :option="routeOption" height="280px" />
      </PanelBox>

      <PanelBox title="巡查任务看板" sub="演示任务" class="span3">
        <div class="kanban">
          <div v-for="col in taskCols" :key="col.status" class="kb-col">
            <div class="kb-head">
              <span class="kb-dot" :style="{ background: statusColor[col.status] }" />
              <span class="kb-name">{{ col.status }}</span>
              <span class="kb-count">{{ col.items.length }}</span>
            </div>
            <div class="kb-cards">
              <div v-for="t in col.items" :key="t.id" class="kb-card">
                <div class="kb-card-name">{{ t.name }}</div>
                <div class="kb-card-meta">{{ t.area }} · {{ t.type }}</div>
                <div class="kb-bar"><div class="kb-fill" :style="{ width: t.progress + '%', background: statusColor[col.status] }" /></div>
              </div>
              <div v-if="!col.items.length" class="kb-empty">暂无任务</div>
            </div>
          </div>
        </div>
      </PanelBox>
    </div>

    <!-- 巡查发现 + 生态修复前后对比 -->
    <div class="grid">
      <PanelBox title="巡查发现" sub="演示发现 · 非真实巡查结果" class="span3">
        <ul class="find-list">
          <li v-for="(f, i) in (uav?.findings || [])" :key="i" class="find-item">
            <span class="find-level" :style="{ color: levelColor[f.level], borderColor: levelColor[f.level] }">{{ f.level }}</span>
            <div class="find-body">
              <div class="find-head">
                <span class="find-type">{{ f.type }}</span>
                <span class="find-area">{{ f.area }}</span>
                <span class="find-status" :style="{ color: statusColor[f.status] }">{{ f.status }}</span>
              </div>
              <div class="find-desc">{{ f.desc }}</div>
            </div>
          </li>
        </ul>
      </PanelBox>

      <PanelBox title="生态修复点位前后对比" sub="演示数据" class="span2">
        <div class="restore-list">
          <div v-for="(r, i) in (uav?.restoration || [])" :key="i" class="restore-item">
            <div class="restore-head">
              <span class="restore-point">{{ r.point }}</span>
              <span class="restore-change">▲ {{ r.change }}</span>
            </div>
            <div class="restore-va">
              <span class="rv">{{ r.before }}</span>
              <span class="rv-arrow">→</span>
              <span class="rv rv-after">{{ r.after }}</span>
            </div>
            <div class="restore-note">{{ r.note }}</div>
          </div>
        </div>
      </PanelBox>
    </div>

    <!-- 巡查能力 -->
    <PanelBox title="巡查能力" sub="空层 · 精细观测">
      <ul class="cap-list">
        <li>农村人居环境整治巡查</li>
        <li>农业面源污染巡查</li>
        <li>河道漂浮物 / 岸线巡查</li>
        <li>生态修复点位前后对比</li>
      </ul>
    </PanelBox>

    <!-- 巡查记录 -->
    <PanelBox title="巡查记录" sub="演示样例 · 非真实巡查结果">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th>区域</th>
              <th>类型</th>
              <th>发现</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(f, i) in (uav?.flights || [])" :key="i">
              <td class="mono">{{ f.date }}</td>
              <td>{{ f.area }}</td>
              <td>{{ f.type }}</td>
              <td>{{ f.finding }}</td>
              <td><span class="demo">{{ f.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelBox>

    <p class="note">{{ uav?.note || '数据未加载' }}</p>
  </div>
</template>

<style scoped>
.uav { display: flex; flex-direction: column; gap: 16px; }
.banner {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; border-radius: 10px;
  background: rgba(250, 178, 25, 0.08); border: 1px solid rgba(250, 178, 25, 0.35);
}
.badge {
  flex-shrink: 0; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;
  color: #06231a; background: #fab219;
}
.banner-text { color: var(--text-secondary); font-size: 13px; }

.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, 1fr); } }
.kpi {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px 18px; display: flex; flex-direction: column; gap: 6px;
}
.kpi-value { font-size: 28px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.kpi-unit { font-size: 13px; font-weight: 500; color: var(--muted); margin-left: 4px; }
.kpi-label { font-size: 13px; color: var(--text-secondary); }

.grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.span2 { grid-column: span 2; }
.span3 { grid-column: span 3; }
@media (max-width: 1000px) { .grid { grid-template-columns: 1fr; } .span2, .span3 { grid-column: span 1; } }

.kanban { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; height: 100%; }
.kb-col { display: flex; flex-direction: column; gap: 10px; }
.kb-head { display: flex; align-items: center; gap: 8px; }
.kb-dot { width: 8px; height: 8px; border-radius: 50%; }
.kb-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.kb-count { font-size: 12px; color: var(--muted); }
.kb-cards { display: flex; flex-direction: column; gap: 8px; }
.kb-card {
  background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px;
  padding: 10px 12px; display: flex; flex-direction: column; gap: 6px;
}
.kb-card-name { font-size: 13px; color: var(--text-primary); font-weight: 600; }
.kb-card-meta { font-size: 12px; color: var(--muted); }
.kb-bar { height: 5px; background: var(--surface); border-radius: 3px; overflow: hidden; }
.kb-fill { height: 100%; border-radius: 3px; }
.kb-empty { font-size: 12px; color: var(--muted); padding: 8px 0; }

.find-list { list-style: none; display: flex; flex-direction: column; gap: 12px; padding: 4px 2px; }
.find-item { display: flex; gap: 12px; align-items: flex-start; }
.find-level {
  flex-shrink: 0; margin-top: 2px; padding: 1px 10px; border-radius: 20px;
  font-size: 12px; font-weight: 600; border: 1px solid;
}
.find-body { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.find-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.find-type { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.find-area { font-size: 12px; color: var(--text-secondary); }
.find-status { font-size: 12px; margin-left: auto; }
.find-desc { font-size: 12px; color: var(--muted); }

.restore-list { display: flex; flex-direction: column; gap: 12px; padding: 4px 2px; }
.restore-item {
  border: 1px solid var(--border); border-radius: 8px; padding: 12px;
  display: flex; flex-direction: column; gap: 8px;
}
.restore-head { display: flex; justify-content: space-between; align-items: center; }
.restore-point { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.restore-change { font-size: 12px; font-weight: 700; color: #2fd08b; }
.restore-va { display: flex; align-items: center; gap: 10px; }
.rv { font-size: 13px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.rv-after { color: #2fd08b; font-weight: 600; }
.rv-arrow { color: var(--muted); }
.restore-note { font-size: 12px; color: var(--muted); }

.cap-list { list-style: none; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 6px 2px; }
@media (max-width: 900px) { .cap-list { grid-template-columns: repeat(2, 1fr); } }
.cap-list li { color: var(--text-secondary); font-size: 13px; padding-left: 18px; position: relative; }
.cap-list li::before { content: '·'; position: absolute; left: 4px; color: var(--brand); font-weight: 700; }

.table-wrap { overflow: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }
th { color: var(--muted); font-weight: 600; background: var(--surface-2); }
td { color: var(--text-secondary); }
.mono {
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  color: var(--text-primary); font-variant-numeric: tabular-nums;
}
.demo {
  font-size: 12px; color: #fab219;
  border: 1px solid rgba(250, 178, 25, 0.5); border-radius: 20px; padding: 2px 10px;
}
.note { color: var(--muted); font-size: 12px; }
</style>
