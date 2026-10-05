<script setup>
import { computed, onMounted } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import PanelBox from '../components/PanelBox.vue'
import StatCard from '../components/StatCard.vue'
import { dimensions, comprehensiveScore, trend, compliance, stations, alerts } from '../data/mock'
import { remoteData, fetchRemoteData } from '../data/remote'

onMounted(fetchRemoteData)

const AXIS = {
  axisLine: { lineStyle: { color: '#383835' } },
  axisLabel: { color: '#898781' },
  splitLine: { lineStyle: { color: '#2c2c2a' } },
}

const radarOption = computed(() => ({
  tooltip: {},
  radar: {
    indicator: dimensions.map((d) => ({ name: d.name, max: 100 })),
    radius: '68%',
    axisName: { color: '#c3c2b7' },
    splitArea: { areaStyle: { color: ['transparent'] } },
    splitLine: { lineStyle: { color: '#2c2c2a' } },
    axisLine: { lineStyle: { color: '#2c2c2a' } },
  },
  series: [{
    type: 'radar',
    data: [{
      value: dimensions.map((d) => d.score),
      name: '五维健康度',
      areaStyle: { color: 'rgba(47, 208, 139, 0.25)' },
      lineStyle: { color: '#2fd08b', width: 2 },
      itemStyle: { color: '#2fd08b' },
    }],
  }],
}))

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { textStyle: { color: '#c3c2b7' }, bottom: 0 },
  grid: { left: 8, right: 12, top: 20, bottom: 34, containLabel: true },
  xAxis: { type: 'category', data: trend.months, ...AXIS },
  yAxis: { type: 'value', max: 100, ...AXIS },
  series: trend.series.map((s, i) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.data,
    showSymbol: false,
    lineStyle: { width: 2 },
    itemStyle: { color: ['#3987e5', '#d95926', '#199e70'][i] },
  })),
}))

const complianceOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 8, right: 12, top: 20, bottom: 8, containLabel: true },
  xAxis: { type: 'category', data: compliance.names, ...AXIS },
  yAxis: { type: 'value', max: 100, ...AXIS },
  series: [{
    type: 'bar',
    data: compliance.values,
    barWidth: '46%',
    itemStyle: {
      borderRadius: [4, 4, 0, 0],
      color: (p) => ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181'][p.dataIndex],
    },
  }],
}))

const stationOption = computed(() => {
  const typeColor = { '大气站': '#3987e5', '水质站': '#d95926', '土壤站': '#199e70', '生态站': '#c98500' }
  const types = [...new Set(stations.map((s) => s.type))]
  const seriesByType = types.map((type) => ({
    name: type,
    type: 'scatter',
    data: stations.filter((s) => s.type === type).map((s) => [s.lon, s.lat, s.value, s.name]),
    symbolSize: (v) => 8 + v[2] / 12,
    itemStyle: { color: typeColor[type], opacity: 0.9 },
  }))
  return {
    tooltip: {
      formatter: (p) => `${p.data[3]}<br/>${p.seriesName} · 指数 ${p.data[2]}`,
    },
    legend: { textStyle: { color: '#c3c2b7' }, bottom: 0 },
    grid: { left: 8, right: 12, top: 20, bottom: 34, containLabel: true },
    xAxis: { type: 'value', name: '经度', min: 100.5, max: 108, ...AXIS, nameTextStyle: { color: '#898781' } },
    yAxis: { type: 'value', name: '纬度', min: 24, max: 32, ...AXIS, nameTextStyle: { color: '#898781' } },
    series: seriesByType,
  }
})

const recentAlerts = computed(() => alerts.slice(0, 6))
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
      <div class="hero-value">{{ comprehensiveScore }}</div>
      <div class="hero-foot">
        <span class="hero-tag">较上月 +1.6</span>
        <span class="hero-note">五维加权 · 空天地一体化监测</span>
      </div>
    </div>

    <div class="stats">
      <StatCard v-for="d in dimensions" :key="d.key" :name="d.name" :score="d.score" :delta="d.delta" :color="d.color" />
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
      <PanelBox title="五维综合评分" sub="雷达图">
        <BaseChart :option="radarOption" height="300px" />
      </PanelBox>
      <PanelBox title="近 12 个月生态环境质量趋势" sub="指数 0-100" class="span2">
        <BaseChart :option="trendOption" height="300px" />
      </PanelBox>
      <PanelBox title="监测站点分布" sub="长江上游">
        <BaseChart :option="stationOption" height="300px" />
      </PanelBox>
    </div>

    <div class="grid">
      <PanelBox title="各维度指标达标率" sub="%" class="span2">
        <BaseChart :option="complianceOption" height="260px" />
      </PanelBox>
      <PanelBox title="最新预警" sub="实时" class="span2">
        <div class="alert-list">
          <div v-for="a in recentAlerts" :key="a.time" class="alert-item">
            <span class="lv" :style="{ color: levelColor[a.level], borderColor: levelColor[a.level] }">{{ a.level }}</span>
            <div class="al-body">
              <div class="al-title">{{ a.area }} · {{ a.type }}</div>
              <div class="al-desc">{{ a.desc }}</div>
            </div>
          </div>
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
