<script setup>
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { alertData, fetchAlerts } from '../data/alerts'

const levelOrder = ['红色', '橙色', '黄色', '蓝色']
const levelColor = { '红色': '#d03b3b', '橙色': '#ec835a', '黄色': '#fab219', '蓝色': '#3987e5' }
const statusColor = { '已处理': '#0ca30c', '处理中': '#fab219', '待处理': '#ec835a' }

const list = computed(() => alertData.value.list)
const isMock = computed(() => alertData.value.source === 'mock')
const updatedAt = computed(() => alertData.value.generatedAt || '')

const counts = computed(() => {
  const m = {}
  levelOrder.forEach((l) => (m[l] = list.value.filter((a) => a.level === l).length))
  return m
})
const total = computed(() => list.value.length)

let timer = null
onMounted(() => { fetchAlerts(); timer = setInterval(fetchAlerts, 60000) })
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="alt">
    <div class="topbar">
      <div class="meta">
        <span v-if="isMock" class="badge mock">演示数据 · 未接入实时预警</span>
        <span v-else class="badge live">实时预警 · 规则引擎</span>
        <span v-if="updatedAt" class="updated">数据更新时间 {{ updatedAt }} · 每 60s 自动刷新</span>
      </div>
      <button class="refresh" @click="fetchAlerts">立即刷新</button>
    </div>

    <div class="cards">
      <div v-for="l in levelOrder" :key="l" class="card" :style="{ borderColor: levelColor[l] + '55' }">
        <div class="card-num" :style="{ color: levelColor[l] }">{{ counts[l] }}</div>
        <div class="card-label">{{ l }}预警</div>
      </div>
      <div class="card total">
        <div class="card-num">{{ total }}</div>
        <div class="card-label">预警总数</div>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>区域</th>
            <th>类型</th>
            <th>等级</th>
            <th>状态</th>
            <th>来源</th>
            <th>描述</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in list" :key="a.time + a.type + a.indicator">
            <td class="mono">{{ a.time }}</td>
            <td>{{ a.area }}</td>
            <td>{{ a.type }}</td>
            <td>
              <span class="lv" :style="{ color: levelColor[a.level], borderColor: levelColor[a.level] }">{{ a.level }}</span>
            </td>
            <td><span :style="{ color: statusColor[a.status] }">{{ a.status }}</span></td>
            <td><span class="src">{{ isMock ? '演示' : (a.source || '—') }}</span></td>
            <td class="desc">{{ a.desc }}</td>
          </tr>
          <tr v-if="!list.length">
            <td colspan="7" class="empty">当前无预警事件</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="note">预警由规则引擎按国标阈值（GB3095-2012 / HJ633）与遥感时序趋势实时生成：大气为 AQICN 监测站地面浓度（准实时），水体 / 植被 / 生态为遥感反演（周期更新）。</p>
  </div>
</template>

<style scoped>
.alt { display: flex; flex-direction: column; gap: 16px; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.badge {
  font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px;
}
.badge.live { color: var(--brand); border: 1px solid rgba(47, 208, 139, 0.4); background: rgba(47, 208, 139, 0.08); }
.badge.mock { color: #fab219; border: 1px solid rgba(250, 178, 25, 0.4); background: rgba(250, 178, 25, 0.08); }
.updated { font-size: 12px; color: var(--muted); }
.refresh {
  padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 13px;
  background: var(--surface); border: 1px solid var(--border); color: var(--text-secondary);
}
.refresh:hover { color: var(--text-primary); }

.cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px; display: flex; flex-direction: column; gap: 6px;
}
.card.total { border-color: var(--border); }
.card-num { font-size: 32px; font-weight: 700; font-variant-numeric: tabular-nums; }
.card.total .card-num { color: var(--text-primary); }
.card-label { color: var(--muted); font-size: 13px; }

.table-wrap {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; overflow: auto;
}
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }
th { color: var(--muted); font-weight: 600; background: var(--surface-2); position: sticky; top: 0; }
td { color: var(--text-secondary); }
tbody tr:hover { background: var(--surface-2); }
.mono { font-variant-numeric: tabular-nums; color: var(--text-primary); }
.lv { font-size: 12px; font-weight: 700; border: 1px solid; border-radius: 4px; padding: 1px 8px; }
.desc { color: var(--text-secondary); }
.src { font-size: 12px; color: var(--brand); }
.empty { text-align: center; color: var(--muted); padding: 32px 0; }
.note { color: var(--muted); font-size: 12px; }

@media (max-width: 900px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
