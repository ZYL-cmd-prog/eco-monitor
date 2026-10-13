import { ref } from 'vue'

// 真实治理决策数据：rs-pipeline/decision.py 生成的 decision.json（预警联动 + 五维常态治理建议）。
// 数据未就绪时回退空状态，页面显式标注。
export const decisionData = ref({ summary: '', actions: [], dimensions: [], generatedAt: '', source: 'real' })

export async function fetchDecision() {
  try {
    const res = await fetch('/data/decision.json', { cache: 'no-store' })
    if (res.ok) {
      const j = await res.json()
      if (j && j.summary != null) {
        decisionData.value = { ...j, source: 'real' }
        return decisionData.value
      }
    }
  } catch (e) { /* 回退空状态 */ }
  decisionData.value = { summary: '', actions: [], dimensions: [], generatedAt: '', source: 'mock' }
  return decisionData.value
}
