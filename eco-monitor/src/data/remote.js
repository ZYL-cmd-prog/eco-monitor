import { ref } from 'vue'

// 遥感数据（NDVI / NDWI），来自 public/data/ndvi.json（由 rs-pipeline/export_frontend.py 生成）
// 数据未就绪时保持 null，页面会显示占位，不影响其它 mock 展示。
export const remoteData = ref(null)

export async function fetchRemoteData() {
  try {
    const res = await fetch('/data/ndvi.json')
    if (res.ok) {
      remoteData.value = await res.json()
    }
  } catch (e) {
    remoteData.value = null
  }
  return remoteData.value
}
