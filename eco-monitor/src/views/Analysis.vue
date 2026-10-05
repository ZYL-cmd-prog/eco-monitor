<script setup>
import { computed } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import PanelBox from '../components/PanelBox.vue'
import { prediction, correlation, tracing } from '../data/mock'

const AXIS = {
  axisLine: { lineStyle: { color: '#383835' } },
  axisLabel: { color: '#898781' },
  splitLine: { lineStyle: { color: '#2c2c2a' } },
}

const predOption = computed(() => {
  const n = prediction.history.length
  const hist = prediction.history
  const fut = prediction.future
  const low = prediction.lower
  const up = prediction.upper
  const band = up.map((u, i) => (u == null ? null : +(u - low[i]).toFixed(2)))
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史值', '模型预测', '置信区间'], textStyle: { color: '#c3c2b7' }, bottom: 0 },
    grid: { left: 8, right: 14, top: 20, bottom: 34, containLabel: true },
    xAxis: {
      type: 'category', data: prediction.labels, ...AXIS,
      axisLabel: { color: (v, i) => (i >= n ? '#fab219' : '#898781') },
    },
    yAxis: { type: 'value', max: 100, ...AXIS },
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
      <PanelBox title="生态环境质量预测（Transformer）" sub="历史 + 未来 12 期" class="span2">
        <BaseChart :option="predOption" height="300px" />
      </PanelBox>
      <PanelBox title="多因子相关性矩阵" sub="相关系数 -1 ~ 1" class="span2">
        <BaseChart :option="corrOption" height="300px" />
      </PanelBox>
    </div>

    <div class="grid">
      <PanelBox title="污染源贡献率溯源" sub="%">
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
      <PanelBox title="模型说明" sub="Encoder + Regressor" class="span3">
        <ul class="model-list">
          <li><b>模型框架：</b>Transformer（编码器 + 回归器）</li>
          <li><b>输入通道：</b>1048（多源指标展平特征）</li>
          <li><b>输出通道：</b>12（未来 12 期生态环境质量）</li>
          <li><b>编码层：</b>6 层 · 8 个注意力头 · 前馈网络</li>
          <li><b>任务：</b>多因子耦合诊断 / 时空演变 / 趋势预测 / 风险预警</li>
        </ul>
        <p class="note">预测曲线虚线为模型输出，阴影为置信区间（演示数据）。</p>
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
