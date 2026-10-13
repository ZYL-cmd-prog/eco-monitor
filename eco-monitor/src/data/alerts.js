import { ref } from 'vue'
import { alerts as mockAlerts } from './mock'

// 真实预警数据：rs-pipeline/alerts.py 生成的 alerts.json（定时刷新 + 前端轮询）。
// 数据未就绪 / 为空时回退 mock 演示数据，并在页面显式标注「演示数据」。
export const alertData = ref({ list: [], generatedAt: '', source: 'real' })

export async function fetchAlerts() {
  try {
    const res = await fetch('/data/alerts.json', { cache: 'no-store' })
    if (res.ok) {
      const j = await res.json()
      if (j && Array.isArray(j.alerts)) {
        alertData.value = {
          list: j.alerts,
          generatedAt: j.generatedAt || '',
          source: 'real',
        }
        return alertData.value
      }
    }
  } catch (e) { /* 回退演示数据 */ }
  alertData.value = { list: mockAlerts, generatedAt: '', source: 'mock' }
  return alertData.value
}
