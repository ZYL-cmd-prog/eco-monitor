<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import PanelBox from '../components/PanelBox.vue'
import { prediction as mockPrediction, correlation, tracing } from '../data/mock'

const AXIS = {
  axisLine: { lineStyle: { color: '#383835' } },
  axisLabel: { color: '#898781' },
  splitLine: { lineStyle: { color: '#2c2c2a' } },
}

// 真实预测数据：rs-pipeline/transformer.py（或 baseline.py）生成的 prediction.json；缺失时回退 mock
const prediction = ref(null)
const isReal = ref(false)
const target = ref('ndvi')

onMounted(async () => {
  try {
    const res = await fetch('/data/prediction.json', { cache: 'no-store' })
    if (res.ok) {
      const d = await res.json()
      prediction.value = d
      isReal.value = true
      target.value = targetsOf(d)[0] || 'ndvi'
      return
    }
  } catch (e) { /* 回退 mock */ }
  prediction.value = mockPrediction
})

// 兼容两种格式：多指标 series（transformer.py）与旧平铺格式（baseline.py / mock）
function targetsOf(p) {
  if (p && p.series) return p.targets || Object.keys(p.series)
  if (p && p.labels) return [p.target || 'ndvi']
  return [mockPrediction.target || 'ndvi']
}
function seriesOf(p, t) {
  if (p && p.series) return p.series[t] || p.series[targetsOf(p)[0]] || null
  return p
}
const targets = computed(() => targetsOf(prediction.value))
const isMulti = computed(() => !!(prediction.value && prediction.value.series))

// 把 history/future/置信区间对齐成完整长度（缺失段补 null），兼容旧 mock 的短数组格式
function normalize(p) {
  if (!p || !p.labels) return null
  const L = p.labels.length
  const pad = (arr, toEnd) => {
    let a = (arr || []).slice(0, L)
    if (toEnd && a.length < L && a[0] != null) {
      a = [...Array(L - a.length).fill(null), ...a]
    }
    while (a.length < L) a.push(null)
    return a
  }
  return {
    labels: p.labels,
    history: pad(p.history, false),
    future: pad(p.future, true),
    upper: pad(p.upper, false),
    lower: pad(p.lower, false),
  }
}

const curSeries = computed(() => normalize(seriesOf(prediction.value, target.value)))

const predSub = computed(() => {
  const p = curSeries.value
  if (!p) return '待生成'
  const n = p.history.filter((v) => v != null).length
  const f = p.future.filter((v) => v != null).length
  return `历史 ${n} 期 + 预测 ${f} 期`
})

const predOption = computed(() => {
  const p = curSeries.value
  if (!p) return {}
  const hist = p.history
  const fut = p.future
  const low = p.lower
  const up = p.upper
  const n = hist.filter((v) => v != null).length
  const band = up.map((u, i) => (u == null ? null : +(u - (low[i] ?? u)).toFixed(2)))
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史值', '模型预测', '置信区间'], textStyle: { color: '#c3c2b7' }, bottom: 0 },
    grid: { left: 8, right: 14, top: 20, bottom: 34, containLabel: true },
    xAxis: {
      type: 'category', data: p.labels, ...AXIS,
      axisLabel: { color: (v, i) => (i >= n ? '#fab219' : '#898781') },
    },
    yAxis: { type: 'value', scale: true, ...AXIS },
    series: [
      { name: '历史值', type: 'line', data: hist, showSymbol: false, smooth: true,
        lineStyle: { width: 2, color: '#3987e5' }, itemStyle: { color: '#3987e5' } },
      { name: '置信区间', type: 'line', data: low, stack: 'band', symbol: 'none',
        lineStyle: { opacity: 0 }, areaStyle: { opacity: 0 }, silent: true },
      { name: '置信区间', type: 'line', data: band, stack: 'band', symbol: 'none',
        lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(47, 208, 139, 0.15)' }, silent: true },
      { name: '模型预测', type: 'line', data: fut, showSymbol: false, smooth: true,
        lineStyle: { width: 2, color: '#2fd08b', type: 'dashed' }, itemStyle: { color: '#2fd08b' } },
    ],
  }
})

const modelInfo = computed(() => {
  const p = prediction.value
  if (!p) return []
  const rows = []
  if (p.model) rows.push(['当前模型', p.model])
  if (p.inputChannels != null) rows.push(['输入通道', `${p.inputChannels}（${p.features?.join(' × ') || '多源指标展平'}）`])
  if (p.outputChannels != null) rows.push(['输出通道', `${p.outputChannels}`])
  if (p.horizon != null) rows.push(['预测期数', `未来 ${p.horizon} 期`])
  if (p.generatedAt) rows.push(['生成时间', p.generatedAt])
  return rows
})
const modelNote = computed(() => prediction.value?.note || '')

const corrOption = computed(() => {
  const names = correlation.names
  const data = []
  for (let i = 0; i < names.length; i++)
    for (let j = 0; j < names.length; j++)
      data.push([j, i, +correlation.matrix[i][j].toFixed(2)])
  return {
    tooltip: { formatter: (p) => `${names[p.data[0]]} × ${names[p.data[1]]}<br/>相关系数 ${p.data[2]}` },
    grid: { left: 8, right: 8, top: 8, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: names, ...AXIS, axisLabel: { color: '#898781', rotate: 45 } },
    yAxis: { type: 'category', data: names, ...AXIS },
    visualMap: {
      min: -1, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#256abf', '#383835', '#d03b3b'] },
      textStyle: { color: '#898781' },
    },
    series: [{
      type: 'heatmap', data,
      label: { show: true, color: '#c3c2b7', fontSize: 10 },
      itemStyle: { borderColor: '#1a1a19', borderWidth: 2 },
      emphasis: { itemStyle: { borderColor: '#ffffff' } },
    }],
  }
})
</script>

<template>
  <div class="ana">
    <div class="grid">
      <PanelBox :title="`生态环境质量趋势预测${isMulti ? ' · ' + target : ''}`" :sub="predSub" class="span2">
        <div v-if="isMulti && targets.length > 1" class="target-tabs">
          <button
            v-for="t in targets" :key="t"
            class="tab" :class="{ active: t === target }"
            @click="target = t"
          >{{ t.toUpperCase() }}</button>
        </div>
        <BaseChart :option="predOption" height="300px" />
      </PanelBox>
      <PanelBox title="多因子相关性矩阵" sub="相关系数 -1 ~ 1 · 演示数据" class="span2">
        <BaseChart :option="corrOption" height="300px" />
      </PanelBox>
    </div>

    <div class="grid">
      <PanelBox title="污染源贡献率溯源" sub="贡献率 % · 演示数据">
        <div class="tracing">
          <div v-for="t in tracing" :key="t.source" class="trace-item">
            <div class="trace-head">
              <span class="trace-name">{{ t.source }}</span>
              <span class="trace-val">{{ t.contribution }}%</span>
            </div>
            <div class="trace-bar">
              <div class="trace-fill" :style="{ width: t.contribution + '%' }" />
            </div>
          </div>
        </div>
      </PanelBox>
      <PanelBox title="模型说明" :sub="isReal ? '真实模型' : '演示数据'" class="span3">
        <ul class="model-list">
          <li v-for="[k, v] in modelInfo" :key="k"><b>{{ k }}：</b>{{ v }}</li>
        </ul>
        <p v-if="modelNote" class="note">{{ modelNote }}</p>
        <p class="note">
          虚线为模型预测，阴影为 95% 置信区间。
          <template v-if="isReal">由 rs-pipeline 训练生成；输入为过去时间窗指标序列，输出未来多期生态环境质量。</template>
          <template v-else>当前展示为演示数据，运行 rs-pipeline 后接入真实模型预测。</template>
        </p>
      </PanelBox>
    </div>
  </div>
</template>

<style scoped>
.ana { display: flex; flex-direction: column; gap: 16px; }
.target-tabs { display: flex; gap: 8px; margin-bottom: 6px; }
.tab {
  background: var(--surface-2); border: 1px solid var(--border); color: var(--text-secondary);
  border-radius: 6px; padding: 3px 12px; font-size: 12px; cursor: pointer; font-family: inherit;
}
.tab.active { color: #2fd08b; border-color: #2fd08b; background: rgba(47, 208, 139, 0.10); }

.tracing { display: flex; flex-direction: column; gap: 14px; padding: 6px 2px; }
.trace-item { display: flex; flex-direction: column; gap: 5px; }
.trace-head { display: flex; justify-content: space-between; font-size: 13px; }
.trace-name { color: var(--text-secondary); }
.trace-val { color: var(--text-primary); font-weight: 600; font-variant-numeric: tabular-nums; }
.trace-bar { height: 8px; background: var(--surface-2); border-radius: 4px; overflow: hidden; }
.trace-fill { height: 100%; background: linear-gradient(90deg, #256abf, #3987e5); border-radius: 4px; }

.model-list { list-style: none; display: flex; flex-direction: column; gap: 12px; padding: 6px 2px; }
.model-list li { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.model-list b { color: var(--text-primary); font-weight: 600; }
.note { margin-top: 14px; color: var(--muted); font-size: 12px; }
</style>
