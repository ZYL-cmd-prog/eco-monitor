<script setup>
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { decisionData, fetchDecision } from '../data/decision'

const priorityColor = { '高': '#d03b3b', '中': '#fab219', '低': '#3987e5' }
const levelColor = { '红色': '#d03b3b', '橙色': '#ec835a', '黄色': '#fab219', '蓝色': '#3987e5' }
const statusColor = { '需治理': '#ec835a', '保持监测': '#fab219', '状况良好': '#0ca30c', '—': '#898781' }

const summary = computed(() => decisionData.value.summary)
const actions = computed(() => decisionData.value.actions)
const dimensions = computed(() => decisionData.value.dimensions)
const isMock = computed(() => decisionData.value.source === 'mock')
const updatedAt = computed(() => decisionData.value.generatedAt || '')

let timer = null
onMounted(() => { fetchDecision(); timer = setInterval(fetchDecision, 60000) })
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="dec">
    <div class="topbar">
      <div class="meta">
        <span v-if="isMock" class="badge mock">演示数据 · 决策引擎待接入</span>
        <span v-else class="badge live">实时决策 · 规则引擎</span>
        <span v-if="updatedAt" class="updated">生成时间 {{ updatedAt }} · 每 60s 自动刷新</span>
      </div>
      <button class="refresh" @click="fetchDecision">立即刷新</button>
    </div>

    <div class="summary card">
      <div class="sum-label">总体研判</div>
      <div class="sum-text">{{ summary || '决策引擎运行中，待生成治理建议…' }}</div>
    </div>

    <div class="section">
      <div class="sec-head">
        <span class="sec-title">分级处置方案</span>
        <span class="sec-sub">由实时预警联动生成 · 按优先级排序</span>
      </div>
      <div v-if="actions.length" class="actions">
        <div v-for="(a, i) in actions" :key="i" class="action card">
          <div class="act-head">
            <span class="prio" :style="{ color: priorityColor[a.priority], borderColor: priorityColor[a.priority] }">{{ a.priority }}</span>
            <span class="cat">{{ a.category }}</span>
            <span class="lv" :style="{ color: levelColor[a.level], borderColor: levelColor[a.level] }">{{ a.level }}</span>
            <span class="deadline">{{ a.deadline }}</span>
          </div>
          <div class="trigger">{{ a.trigger }}</div>
          <ul class="measures">
            <li v-for="(m, j) in a.measures" :key="j">{{ m }}</li>
          </ul>
          <div class="act-foot">责任部门：{{ a.responsible }}</div>
        </div>
      </div>
      <div v-else class="empty card">当前无预警，无需联动处置。系统保持常态监测与预防性治理。</div>
    </div>

    <div class="section">
      <div class="sec-head">
        <span class="sec-title">五维常态治理</span>
        <span class="sec-sub">大气 · 水体 · 土壤 · 植被 · 生态</span>
      </div>
      <div class="dims">
        <div v-for="d in dimensions" :key="d.name" class="dim card">
          <div class="dim-head">
            <span class="dim-name">{{ d.name }}</span>
            <span class="dim-status" :style="{ color: statusColor[d.status] }">{{ d.status }}</span>
          </div>
          <div class="dim-signal">{{ d.signal }}</div>
          <div class="dim-sug">{{ d.suggestion }}</div>
        </div>
      </div>
    </div>

    <p class="note">治理决策由规则引擎按「预警联动 + 指标阈值」生成，作为辅助决策建议，不替代人工研判与现场执法。责任部门、处置措施为通用模板，可按属地职责进一步细化。</p>
  </div>
</template>

<style scoped>
.dec { display: flex; flex-direction: column; gap: 16px; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.badge { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
.badge.live { color: var(--brand); border: 1px solid rgba(47, 208, 139, 0.4); background: rgba(47, 208, 139, 0.08); }
.badge.mock { color: #fab219; border: 1px solid rgba(250, 178, 25, 0.4); background: rgba(250, 178, 25, 0.08); }
.updated { font-size: 12px; color: var(--muted); }
.refresh {
  padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 13px;
  background: var(--surface); border: 1px solid var(--border); color: var(--text-secondary);
}
.refresh:hover { color: var(--text-primary); }

.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }

.summary { padding: 18px 20px; display: flex; flex-direction: column; gap: 8px; }
.sum-label { font-size: 13px; color: var(--muted); }
.sum-text { font-size: 16px; color: var(--text-primary); line-height: 1.6; }

.section { display: flex; flex-direction: column; gap: 12px; }
.sec-head { display: flex; align-items: baseline; gap: 12px; }
.sec-title { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.sec-sub { font-size: 12px; color: var(--muted); }

.actions { display: flex; flex-direction: column; gap: 12px; }
.action { padding: 16px 18px; display: flex; flex-direction: column; gap: 10px; }
.act-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.prio, .lv { font-size: 12px; font-weight: 700; border: 1px solid; border-radius: 4px; padding: 1px 8px; }
.cat { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.deadline { margin-left: auto; font-size: 12px; color: var(--muted); }
.trigger { font-size: 13px; color: var(--text-secondary); }
.measures { margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; }
.measures li { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.act-foot { font-size: 12px; color: var(--muted); }

.dims { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
.dim { padding: 16px 18px; display: flex; flex-direction: column; gap: 8px; }
.dim-head { display: flex; align-items: center; justify-content: space-between; }
.dim-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.dim-status { font-size: 12px; font-weight: 600; }
.dim-signal { font-size: 20px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.dim-sug { font-size: 12px; color: var(--muted); line-height: 1.5; }

.empty { padding: 24px; text-align: center; color: var(--muted); font-size: 13px; }
.note { color: var(--muted); font-size: 12px; line-height: 1.6; }
</style>
