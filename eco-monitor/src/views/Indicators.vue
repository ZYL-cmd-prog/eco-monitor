<script setup>
import { ref, computed, onMounted } from 'vue'
import { indicators, dimensions } from '../data/mock'
import { remoteData, fetchRemoteData } from '../data/remote'

onMounted(fetchRemoteData)

const active = ref('全部')
const cats = ['全部', ...dimensions.map((d) => d.name)]

// 遥感实算指标（NDVI / NDWI），从 public/data/ndvi.json 读取
const rsIndicators = computed(() => {
  const d = remoteData.value
  if (!d) return []
  const round = (v) => (v == null ? null : Math.round(v * 1000) / 1000)
  const idx = d.indices || {}
  const ndviVal = d.ndvi?.mean
  const atmo = d.atmosphere || {}
  return [
    { code: 'NDVI', name: '归一化植被指数', category: '植被', value: round(ndviVal), unit: '', level: ndviLevel(ndviVal), trend: 1, source: '遥感' },
    { code: 'NDWI', name: '归一化水体指数', category: '水体', value: round(d.ndwi?.mean), unit: '', level: ndwiLevel(d.ndwi?.mean), trend: 0, source: '遥感' },
    { code: 'EVI', name: '增强植被指数', category: '植被', value: round(idx.evi?.mean), unit: '', level: eviLevel(idx.evi?.mean), trend: 1, source: '遥感' },
    { code: 'FVC', name: '植被覆盖度', category: '植被', value: round(idx.fvc?.mean), unit: '', level: fvcLevel(idx.fvc?.mean), trend: 1, source: '遥感' },
    { code: 'LAI', name: '叶面积指数', category: '植被', value: round(idx.lai?.mean), unit: '', level: laiLevel(idx.lai?.mean), trend: 1, source: '遥感' },
    { code: 'NDBSI', name: '干度', category: '生态', value: round(idx.ndbsi?.mean), unit: '', level: ndbsiLevel(idx.ndbsi?.mean), trend: 0, source: '遥感' },
    { code: 'WET', name: '湿度', category: '生态', value: round(idx.wet?.mean), unit: '', level: wetLevel(idx.wet?.mean), trend: 0, source: '遥感' },
    { code: 'VI', name: '绿度', category: '生态', value: round(ndviVal), unit: '', level: ndviLevel(ndviVal), trend: 1, source: '遥感' },
    { code: 'LST', name: '热度', category: '生态', value: round(idx.lst?.mean), unit: '°C', level: lstLevel(idx.lst?.mean), trend: 0, source: '遥感' },
    { code: 'NO2', name: '二氧化氮柱浓度', category: '大气', value: round(atmo.no2?.median), unit: atmo.no2?.unit || 'μmol/m²', level: no2Level(atmo.no2?.median), trend: 0, source: '遥感' },
    { code: 'SO2', name: '二氧化硫柱浓度', category: '大气', value: round(atmo.so2?.median), unit: atmo.so2?.unit || 'μmol/m²', level: so2Level(atmo.so2?.median), trend: 0, source: '遥感' },
    { code: 'O3', name: '臭氧总柱', category: '大气', value: round(atmo.o3?.median), unit: atmo.o3?.unit || 'DU', level: o3Level(atmo.o3?.median), trend: 0, source: '遥感' },
  ]
})

function ndviLevel(v) {
  if (v == null) return '—'
  if (v >= 0.6) return '良好'
  if (v >= 0.3) return '正常'
  return '偏低'
}
function ndwiLevel(v) {
  if (v == null) return '—'
  if (v >= 0.2) return '良好'
  if (v >= 0) return '正常'
  return '偏低'
}
function eviLevel(v) {
  if (v == null) return '—'
  if (v >= 0.5) return '良好'
  if (v >= 0.2) return '正常'
  return '偏低'
}
function ndbsiLevel(v) {
  if (v == null) return '—'
  if (v <= -0.1) return '优'
  if (v <= 0.15) return '正常'
  return '偏高'
}
function wetLevel(v) {
  if (v == null) return '—'
  if (v >= -0.15) return '良好'
  if (v >= -0.4) return '正常'
  return '偏低'
}
function fvcLevel(v) {
  if (v == null) return '—'
  if (v >= 0.7) return '良好'
  if (v >= 0.4) return '正常'
  return '偏低'
}
function laiLevel(v) {
  if (v == null) return '—'
  if (v >= 3) return '良好'
  if (v >= 1.5) return '正常'
  return '偏低'
}
function lstLevel(v) {
  if (v == null) return '—'
  if (v <= 35) return '正常'
  if (v <= 45) return '偏高'
  return '高'
}
function no2Level(v) {
  if (v == null) return '—'
  if (v < 15) return '优'
  if (v < 30) return '良'
  if (v < 60) return '偏高'
  return '高'
}
function so2Level(v) {
  if (v == null) return '—'
  if (v < 2) return '优'
  if (v < 5) return '良'
  return '偏高'
}
function o3Level(v) {
  if (v == null) return '—'
  if (v < 250) return '偏低'
  if (v <= 350) return '正常'
  return '偏高'
}

const all = computed(() => {
  const real = rsIndicators.value
  const realByCode = Object.fromEntries(real.map((i) => [i.code, i]))
  // 用遥感实算值覆盖同编码的演示项（EVI/干度/湿度），其余演示项保留；NDVI/NDWI 为新增
  const merged = indicators.map((i) => realByCode[i.code] || i)
  const added = real.filter((i) => !indicators.some((m) => m.code === i.code))
  return [...merged, ...added]
})
const filtered = computed(() =>
  active.value === '全部' ? all.value : all.value.filter((i) => i.category === active.value)
)

const catColor = { '大气': '#3987e5', '水体': '#d95926', '土壤': '#199e70', '植被': '#c98500', '生态': '#d55181' }

function levelColor(l) {
  if (['优', '良好', '安全'].includes(l)) return '#0ca30c'
  if (['良', '正常', '中性'].includes(l)) return '#fab219'
  return '#ec835a'
}
function trendText(t) { return t > 0 ? '↑' : t < 0 ? '↓' : '→' }
function trendColor(t) { return t > 0 ? '#0ca30c' : t < 0 ? '#d03b3b' : '#898781' }
</script>

<template>
  <div class="ind">
    <div class="toolbar">
      <button v-for="c in cats" :key="c" class="cat" :class="{ active: active === c }" @click="active = c">
        {{ c }}
      </button>
      <span class="count">共 {{ filtered.length }} 项指标</span>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>指标编码</th>
            <th>指标名称</th>
            <th>类别</th>
            <th>当前值</th>
            <th>单位</th>
            <th>质量等级</th>
            <th>趋势</th>
            <th>来源</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in filtered" :key="i.code">
            <td class="mono">{{ i.code }}</td>
            <td>{{ i.name }}</td>
            <td>
              <span class="chip" :style="{ color: catColor[i.category], borderColor: catColor[i.category] + '66' }">{{ i.category }}</span>
            </td>
            <td class="mono">{{ i.value }}</td>
            <td class="unit">{{ i.unit || '—' }}</td>
            <td><span class="level" :style="{ color: levelColor(i.level) }">{{ i.level }}</span></td>
            <td :style="{ color: trendColor(i.trend) }" class="trend">{{ trendText(i.trend) }}</td>
            <td><span class="src" :class="{ remote: i.source === '遥感' }">{{ i.source === '遥感' ? '遥感' : '演示' }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="note">植被与生态类指数（NDVI / NDWI / EVI / FVC / LAI / 绿度 / 干度 / 湿度 / 热度）来自 Sentinel-2 / Landsat 遥感实算；大气 NO2 / SO2 / O3 为 Sentinel-5P 柱浓度实算（非地面 μg/m³ 浓度）；AQI、水质、土壤类仍需对接监测站点（演示数据）。</p>
  </div>
</template>

<style scoped>
.ind { display: flex; flex-direction: column; gap: 16px; }
.toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.cat {
  padding: 7px 16px; border-radius: 8px; cursor: pointer;
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text-secondary); font-size: 13px;
}
.cat:hover { color: var(--text-primary); }
.cat.active {
  background: rgba(47, 208, 139, 0.12); color: var(--brand);
  border-color: rgba(47, 208, 139, 0.4);
}
.count { margin-left: auto; color: var(--muted); font-size: 13px; }
.table-wrap {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; overflow: auto;
}
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }
th { color: var(--muted); font-weight: 600; background: var(--surface-2); position: sticky; top: 0; }
td { color: var(--text-secondary); }
tbody tr:hover { background: var(--surface-2); }
.mono {
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  font-variant-numeric: tabular-nums; color: var(--text-primary);
}
.unit { color: var(--muted); }
.chip { font-size: 12px; border: 1px solid; border-radius: 20px; padding: 2px 10px; }
.level { font-weight: 600; }
.trend { font-weight: 700; font-size: 16px; }
.src { font-size: 12px; color: var(--muted); }
.src.remote { color: var(--brand); }
.note { color: var(--muted); font-size: 12px; }
</style>
