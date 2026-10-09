<script setup>
import { ref, onMounted } from 'vue'
import PanelBox from '../components/PanelBox.vue'

// 无人机巡查数据：rs-pipeline/uav.py 生成的 uav.json（演示样例）
const uav = ref(null)

onMounted(async () => {
  try {
    const res = await fetch('/data/uav.json')
    if (res.ok) uav.value = await res.json()
  } catch (e) {
    uav.value = null
  }
})
</script>

<template>
  <div class="uav">
    <div class="banner">
      <span class="badge">演示样例</span>
      <span class="banner-text">无人机巡查模块（「空—天—地」之空层）—— 待接入真实无人机正射影像，当前为模块框架演示</span>
    </div>

    <div class="grid">
      <PanelBox title="无人机正射影像接入点" sub="真实影像接入后展示" class="span2">
        <div class="placeholder">
          <div class="ph-icon">✈</div>
          <div class="ph-text">待接入真实无人机正射影像（GeoTIFF）</div>
          <div class="ph-sub">接入后：高分辨率 NDVI / 水面漂浮物 / 垃圾堆放点识别</div>
        </div>
      </PanelBox>
      <PanelBox title="巡查能力" sub="空层 · 精细观测" class="span2">
        <ul class="cap-list">
          <li>农村人居环境整治巡查</li>
          <li>农业面源污染巡查</li>
          <li>河道漂浮物 / 岸线巡查</li>
          <li>生态修复点位前后对比</li>
        </ul>
      </PanelBox>
    </div>

    <PanelBox title="巡查记录" sub="演示样例 · 非真实巡查结果">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th>区域</th>
              <th>类型</th>
              <th>发现</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(f, i) in (uav?.flights || [])" :key="i">
              <td class="mono">{{ f.date }}</td>
              <td>{{ f.area }}</td>
              <td>{{ f.type }}</td>
              <td>{{ f.finding }}</td>
              <td><span class="demo">{{ f.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelBox>

    <p class="note">{{ uav?.note || '数据未加载' }}</p>
  </div>
</template>

<style scoped>
.uav { display: flex; flex-direction: column; gap: 16px; }
.banner {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; border-radius: 10px;
  background: rgba(250, 178, 25, 0.08); border: 1px solid rgba(250, 178, 25, 0.35);
}
.badge {
  flex-shrink: 0; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;
  color: #06231a; background: #fab219;
}
.banner-text { color: var(--text-secondary); font-size: 13px; }

.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }

.placeholder {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; min-height: 180px; text-align: center; padding: 16px;
  border: 1px dashed var(--border); border-radius: 10px;
}
.ph-icon { font-size: 40px; opacity: 0.5; }
.ph-text { color: var(--text-primary); font-size: 14px; }
.ph-sub { color: var(--muted); font-size: 12px; }

.cap-list { list-style: none; display: flex; flex-direction: column; gap: 12px; padding: 6px 2px; }
.cap-list li { color: var(--text-secondary); font-size: 13px; padding-left: 18px; position: relative; }
.cap-list li::before { content: '·'; position: absolute; left: 4px; color: var(--brand); font-weight: 700; }

.table-wrap { overflow: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }
th { color: var(--muted); font-weight: 600; background: var(--surface-2); }
td { color: var(--text-secondary); }
.mono {
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  color: var(--text-primary); font-variant-numeric: tabular-nums;
}
.demo {
  font-size: 12px; color: #fab219;
  border: 1px solid rgba(250, 178, 25, 0.5); border-radius: 20px; padding: 2px 10px;
}
.note { color: var(--muted); font-size: 12px; }
</style>
