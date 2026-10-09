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

// 真实预测数据：rs-pipeline/baseline.py 生成的 prediction.json；缺失时回退 mock
const prediction = ref(null)

onMounted(async () => {
  try {
    const res = await fetch('/data/prediction.json')
    if (res.ok) {
      prediction.value = await res.json()
      return
    }
  } catch (e) { /* 回退 mock */ }
  prediction.value = mockPrediction
})

// 把 history/future/置信区间对齐成完整长度（缺失段补 null），兼容旧 mock 的短数组格式
function normalize(p) {
  if (!p || !p.labels) return null
  const L = p.labels.length
  const pad = (arr, toEnd) => {
    let a = (arr || []).slice(0, L)
    if (toEnd && a.length < L && a[0] != null) {
      // 旧 mock 的 future 是 12 个值、无前导 null，整体移到尾部
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

const predOption = computed(() => {
  const p = normalize(prediction.value)
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
      <PanelBox title="生态环境质量趋势预测" sub="历史 12 期 + 未来 12 期" class="span2">
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
      <PanelBox title="模型说明" sub="基线 → Transformer" class="span3">
        <ul class="model-list">
          <li><b>当前模型：</b>线性趋势基线（Baseline 1，真实月度 NDVI）</li>
          <li><b>目标架构：</b>Transformer（编码器 + 回归器，文档 2.3）</li>
          <li><b>输入通道：</b>1048（多源指标展平特征，目标）</li>
          <li><b>输出通道：</b>12（未来 12 期生态环境质量）</li>
          <li><b>编码层：</b>6 层 · 8 个注意力头 · 前馈网络（目标）</li>
          <li><b>任务：</b>多因子耦合诊断 / 时空演变 / 趋势预测 / 风险预警</li>
        </ul>
        <p class="note">虚线为模型预测，阴影为 95% 置信区间。当前为线性趋势基线，接入完整历史时序后逐步升级到 Transformer。</p>
      </PanelBox>
    </div>
  </div>
</template>

<style scoped>
.ana { display: flex; flex-direction: column; gap: 16px; }
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
