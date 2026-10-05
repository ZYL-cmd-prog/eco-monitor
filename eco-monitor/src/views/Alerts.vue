<script setup>
import { computed } from 'vue'
import { alerts } from '../data/mock'

const levelOrder = ['红色', '橙色', '黄色', '蓝色']
const levelColor = { '红色': '#d03b3b', '橙色': '#ec835a', '黄色': '#fab219', '蓝色': '#3987e5' }
const statusColor = { '已处理': '#0ca30c', '处理中': '#fab219', '待处理': '#ec835a' }

const counts = computed(() => {
  const m = {}
  levelOrder.forEach((l) => (m[l] = alerts.filter((a) => a.level === l).length))
  return m
})
const total = computed(() => alerts.length)
</script>

<template>
  <div class="alt">
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
            <th>描述</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in alerts" :key="a.time">
            <td class="mono">{{ a.time }}</td>
            <td>{{ a.area }}</td>
            <td>{{ a.type }}</td>
            <td>
              <span class="lv" :style="{ color: levelColor[a.level], borderColor: levelColor[a.level] }">{{ a.level }}</span>
            </td>
            <td><span :style="{ color: statusColor[a.status] }">{{ a.status }}</span></td>
            <td class="desc">{{ a.desc }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.alt { display: flex; flex-direction: column; gap: 16px; }
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

@media (max-width: 900px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
