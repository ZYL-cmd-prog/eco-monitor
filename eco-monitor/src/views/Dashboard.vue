<script setup>
import { computed, onMounted } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import PanelBox from '../components/PanelBox.vue'
import StatCard from '../components/StatCard.vue'
import { stations } from '../data/mock'
import { remoteData, fetchRemoteData } from '../data/remote'
import { alertData, fetchAlerts } from '../data/alerts'
import { buildScores } from '../data/scores'

onMounted(() => { fetchRemoteData(); fetchAlerts() })

const AXIS = {
  axisLine: { lineStyle: { color: '#383835' } },
  axisLabel: { color: '#898781' },
  splitLine: { lineStyle: { color: '#2c2c2a' } },
}

// 由真实数据构建五维评分 / 综合指数 / 达标率
const scores = computed(() => buildScores(remoteData.value))
const dims = computed(() => scores.value.dims)

const radarOption = computed(() => ({
  tooltip: {},
  radar: {
    indicator: dims.value.map((d) => ({ name: d.name, max: 100 })),
    radius: '68%',
    axisName: { color: '#c3c2b7' },
    splitArea: { areaStyle: { color: ['transparent'] } },
    splitLine: { lineStyle: { color: '#2c2c2a' } },
    axisLine: { lineStyle: { color: '#2c2c2a' } },
  },
  series: [{
    type: 'radar',
    data: [{
      value: dims.value.map((d) => d.score),
      name: '五维健康度',
      areaStyle: { color: 'rgba(47, 208, 139, 0.25)' },
      lineStyle: { color: '#2fd08b', width: 2 },
      itemStyle: { color: '#2fd08b' },
    }],
  }],
}))

const complianceOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 8, right: 12, top: 20, bottom: 8, containLabel: true },
  xAxis: { type: 'category', data: scores.value.compliance.names, ...AXIS },
  yAxis: { type: 'value', max: 100, ...AXIS },
  series: [{
    type: 'bar',
    data: scores.value.compliance.values,
    barWidth: '46%',
    itemStyle: {
      borderRadius: [4, 4, 0, 0],
      color: (p) => ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181'][p.dataIndex],
    },
  }],
}))

// 植被长势趋势：优先长期 MODIS（2000–今），回退近期 Sentinel-2 时序
const trendData = computed(() => {
  const mh = remoteData.value?.modisHistory || []
  if (mh.length) return { labels: mh.map((t) => t.month), ndvi: mh.map((t) => t.ndvi), evi: mh.map((t) => t.evi), long: true }
  const ts = remoteData.value?.timeseries || []
  if (ts.length) return { labels: ts.map((t) => t.month), ndvi: ts.map((t) => t.ndvi), evi: null, long: false }
  return { labels: [], ndvi: [], evi: null, long: false }
})
const trendOption = computed(() => {
  const t = trendData.value
  const series = [{
    name: 'NDVI', type: 'line', smooth: true, data: t.ndvi, showSymbol: false,
    lineStyle: { width: 2 }, itemStyle: { color: '#199e70' },
  }]
  if (t.evi && t.evi.some((v) => v != null)) {
    series.push({
      name: 'EVI', type: 'line', smooth: true, data: t.evi, showSymbol: false,
      lineStyle: { width: 2 }, itemStyle: { color: '#c98500' },
    })
  }
  return {
    tooltip: { trigger: 'axis' },
    legend: { textStyle: { color: '#c3c2b7' }, bottom: 0 },
    grid: { left: 8, right: 12, top: 20, bottom: 34, containLabel: true },
    xAxis: { type: 'category', data: t.labels, ...AXIS },
    yAxis: { type: 'value', scale: true, ...AXIS },
    series,
  }
})
const trendSub = computed(() => (trendData.value.long ? `${trendData.value.labels.length} 期月度 NDVI/EVI` : (trendData.value.labels.length ? `近 ${trendData.value.labels.length} 期 NDVI` : '待接入时序数据')))

// 站点分布：真实 AQICN 监测站（按 AQI 分级着色），缺失回退演示站点
const stationsReal = computed(() => (remoteData.value?.stations || []).filter((s) => s.aqi != null))
const stationSub = computed(() => (stationsReal.value.length ? 'AQICN 实时监测站' : '示范站点 · 演示数据'))
const stationOption = computed(() => {
  const grid = { left: 8, right: 12, top: 20, bottom: 34, containLabel: true }
  const xAxis = { type: 'value', name: '经度', min: 100.5, max: 108, ...AXIS, nameTextStyle: { color: '#898781' } }
  const yAxis = { type: 'value', name: '纬度', min: 24, max: 32, ...AXIS, nameTextStyle: { color: '#898781' } }

  if (stationsReal.value.length) {
    const color = { '优': '#0ca30c', '良': '#fab219', '轻度污染': '#ec835a', '中度污染': '#d03b3b', '重度污染': '#8b2e2e' }
    const groups = { '优': [], '良': [], '轻度污染': [], '中度污染': [], '重度污染': [] }
    stationsReal.value.forEach((s) => {
      const g = s.aqi <= 50 ? '优' : s.aqi <= 100 ? '良' : s.aqi <= 150 ? '轻度污染' : s.aqi <= 200 ? '中度污染' : '重度污染'
      groups[g].push([s.lon, s.lat, s.aqi, s.name])
    })
    return {
      tooltip: { formatter: (p) => `${p.data[3]}<br/>AQI ${p.data[2]} · ${p.seriesName}` },
      legend: { textStyle: { color: '#c3c2b7' }, bottom: 0 },
      grid, xAxis, yAxis,
      series: Object.keys(groups).filter((k) => groups[k].length).map((k) => ({
        name: k, type: 'scatter', data: groups[k],
        symbolSize: (v) => 8 + Math.min(v[2] / 25, 10),
        itemStyle: { color: color[k], opacity: 0.9 },
      })),
    }
  }
  const typeColor = { '大气站': '#3987e5', '水质站': '#d95926', '土壤站': '#199e70', '生态站': '#c98500' }
  const types = [...new Set(stations.map((s) => s.type))]
  return {
    tooltip: { formatter: (p) => `${p.data[3]}<br/>${p.seriesName} · 指数 ${p.data[2]}` },
    legend: { textStyle: { color: '#c3c2b7' }, bottom: 0 },
    grid, xAxis, yAxis,
    series: types.map((type) => ({
      name: type, type: 'scatter',
      data: stations.filter((s) => s.type === type).map((s) => [s.lon, s.lat, s.value, s.name]),
      symbolSize: (v) => 8 + v[2] / 12,
      itemStyle: { color: typeColor[type], opacity: 0.9 },
    })),
  }
})

const recentAlerts = computed(() => alertData.value.list.slice(0, 6))
const alertsMock = computed(() => alertData.value.source === 'mock')
const levelColor = { '红色': '#d03b3b', '橙色': '#ec835a', '黄色': '#fab219', '蓝色': '#3987e5' }

// 遥感实算指数（NDVI / NDWI）
const ndvi = computed(() => remoteData.value?.ndvi ?? null)
const ndwi = computed(() => remoteData.value?.ndwi ?? null)

const rsTrendOption = computed(() => {
  const ts = remoteData.value?.timeseries ?? []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['NDVI', 'NDWI'], textStyle: { color: '#c3c2b7' }, bottom: 0 },
    grid: { left: 8, right: 12, top: 20, bottom: 34, containLabel: true },
    xAxis: { type: 'category', data: ts.map((t) => t.month), ...AXIS },
    yAxis: { type: 'value', min: -1, max: 1, ...AXIS },
    series: [
      { name: 'NDVI', type: 'line', smooth: true, data: ts.map((t) => t.ndvi), showSymbol: false, lineStyle: { width: 2 }, itemStyle: { color: '#199e70' } },
      { name: 'NDWI', type: 'line', smooth: true, data: ts.map((t) => t.ndwi), showSymbol: false, lineStyle: { width: 2 }, itemStyle: { color: '#3987e5' } },
    ],
  }
})
</script>

<template>
  <div class="dash">
    <div class="hero">
      <div class="hero-label">综合生态环境质量指数</div>
      <div class="hero-value">{{ scores.comprehensive }}</div>
      <div class="hero-foot">
        <span v-if="scores.ndviDelta != null" class="hero-tag">植被 NDVI 较上月 {{ scores.ndviDelta >= 0 ? '+' : '' }}{{ scores.ndviDelta }}</span>
        <span class="hero-note" :class="{ demo: !scores.isReal }">{{ scores.isReal ? '五维等权加权 · 真实监测 / 遥感反演' : '演示数据 · 遥感数据待接入' }}</span>
      </div>
    </div>

    <div class="stats">
      <StatCard v-for="d in dims" :key="d.key" :name="d.name" :score="d.score" delta="" :color="d.color" />
    </div>

    <div class="rs-band">
      <div class="rs-head">
        <span class="rs-title">遥感监测指数</span>
        <span class="rs-sub">{{ remoteData ? `${remoteData.satellite} · ${remoteData.date}` : 'Sentinel-2 · 待接入（运行 rs-pipeline）' }}</span>
      </div>
      <div class="grid">
        <PanelBox title="NDVI 植被指数" sub="归一化植被指数 -1~1">
          <div class="rs-card">
            <img v-if="ndvi?.image" :src="ndvi.image" class="rs-img" alt="NDVI" />
            <div v-else class="rs-empty">暂无影像 · 运行 rs-pipeline/export_frontend.py 生成</div>
            <div v-if="ndvi" class="rs-stats">
              <div class="rs-stat"><span>均值</span><b>{{ ndvi.mean.toFixed(3) }}</b></div>
              <div class="rs-stat"><span>最小</span><b>{{ ndvi.min.toFixed(3) }}</b></div>
              <div class="rs-stat"><span>最大</span><b>{{ ndvi.max.toFixed(3) }}</b></div>
              <div class="rs-stat"><span>植被覆盖</span><b>{{ (ndvi.vegetationRatio * 100).toFixed(0) }}%</b></div>
            </div>
          </div>
        </PanelBox>
        <PanelBox title="NDWI 水体指数" sub="归一化水体指数 -1~1">
          <div class="rs-card">
            <img v-if="ndwi?.image" :src="ndwi.image" class="rs-img" alt="NDWI" />
            <div v-else class="rs-empty">暂无影像 · 运行 rs-pipeline/export_frontend.py 生成</div>
            <div v-if="ndwi" class="rs-stats">
              <div class="rs-stat"><span>均值</span><b>{{ ndwi.mean.toFixed(3) }}</b></div>
              <div class="rs-stat"><span>最小</span><b>{{ ndwi.min.toFixed(3) }}</b></div>
              <div class="rs-stat"><span>最大</span><b>{{ ndwi.max.toFixed(3) }}</b></div>
              <div class="rs-stat"><span>水体占比</span><b>{{ (ndwi.waterRatio * 100).toFixed(1) }}%</b></div>
            </div>
          </div>
        </PanelBox>
        <PanelBox title="NDVI / NDWI 季节变化" sub="遥感指数时序" class="span2">
          <BaseChart :option="rsTrendOption" height="220px" />
        </PanelBox>
      </div>
    </div>

    <div class="grid">
      <PanelBox title="五维综合评分" :sub="scores.isReal ? '真实数据加权' : '演示数据'">
        <BaseChart :option="radarOption" height="300px" />
      </PanelBox>
      <PanelBox title="生态环境质量趋势" :sub="trendSub" class="span2">
        <BaseChart :option="trendOption" height="300px" />
      </PanelBox>
      <PanelBox title="监测站点分布" :sub="stationSub">
        <BaseChart :option="stationOption" height="300px" />
      </PanelBox>
    </div>

    <div class="grid">
      <PanelBox title="各维度指标达标率" :sub="scores.isReal ? '分数 ≥ 60 占比' : '演示数据'" class="span2">
        <BaseChart :option="complianceOption" height="260px" />
      </PanelBox>
      <PanelBox title="最新预警" :sub="alertsMock ? '实时 · 演示数据' : '实时 · 规则引擎'" class="span2">
        <div class="alert-list">
          <div v-for="a in recentAlerts" :key="a.time + a.type + (a.indicator || '')" class="alert-item">
            <span class="lv" :style="{ color: levelColor[a.level], borderColor: levelColor[a.level] }">{{ a.level }}</span>
            <div class="al-body">
              <div class="al-title">{{ a.area }} · {{ a.type }}</div>
              <div class="al-desc">{{ a.desc }}</div>
            </div>
          </div>
          <div v-if="!recentAlerts.length" class="alert-empty">当前无预警事件</div>
        </div>
      </PanelBox>
    </div>
  </div>
</template>

<style scoped>
.dash { display: flex; flex-direction: column; gap: 16px; }
.hero {
  background: linear-gradient(135deg, rgba(47, 208, 139, 0.14), rgba(56, 189, 248, 0.10));
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hero-label { color: var(--text-secondary); font-size: 13px; }
.hero-value {
  font-size: 46px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.hero-foot { display: flex; gap: 16px; align-items: center; }
.hero-tag { color: var(--good); font-size: 13px; font-weight: 600; }
.hero-note { color: var(--muted); font-size: 12px; }
.hero-note.demo { color: #fab219; }

.rs-band { display: flex; flex-direction: column; gap: 12px; }
.rs-head { display: flex; align-items: baseline; gap: 12px; }
.rs-title { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.rs-sub { font-size: 12px; color: var(--muted); }
.rs-card { display: flex; flex-direction: column; gap: 10px; }
.rs-img { width: 100%; border-radius: 8px; border: 1px solid var(--border); display: block; }
.rs-empty {
  display: grid; place-items: center; height: 120px; text-align: center;
  color: var(--muted); font-size: 12px;
  border: 1px dashed var(--border); border-radius: 8px;
}
.rs-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.rs-stat {
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 6px; text-align: center;
  display: flex; flex-direction: column; gap: 4px;
}
.rs-stat span { color: var(--muted); font-size: 11px; }
.rs-stat b { color: var(--text-primary); font-size: 15px; font-variant-numeric: tabular-nums; }

.alert-list { display: flex; flex-direction: column; gap: 10px; }
.alert-empty { color: var(--muted); font-size: 12px; padding: 8px 0; }
.alert-item { display: flex; gap: 10px; align-items: flex-start; }
.lv {
  flex-shrink: 0; font-size: 12px; font-weight: 700;
  border: 1px solid; border-radius: 4px; padding: 1px 6px;
}
.al-body { min-width: 0; }
.al-title { font-size: 13px; color: var(--text-primary); }
.al-desc {
  font-size: 12px; color: var(--muted);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
</style>
