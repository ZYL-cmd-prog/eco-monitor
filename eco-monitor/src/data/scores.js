import { dimensions as mockDims, comprehensiveScore as mockComprehensive, compliance as mockCompliance } from './mock'

// 指标值 → 0-100 健康度分数（越高越好），线性插值。阈值与 Indicators.vue 的质量分级一致。
function lerp(anchors, v) {
  if (v == null || Number.isNaN(v)) return null
  const first = anchors[0]
  const last = anchors[anchors.length - 1]
  if (v <= first[0]) return first[1]
  if (v >= last[0]) return last[1]
  for (let i = 0; i < anchors.length - 1; i++) {
    const [x0, y0] = anchors[i]
    const [x1, y1] = anchors[i + 1]
    if (v >= x0 && v <= x1) return y0 + ((v - x0) / (x1 - x0)) * (y1 - y0)
  }
  return null
}
const clamp = (v) => (v == null ? null : Math.max(0, Math.min(100, v)))

// 大气污染物地面浓度（AQICN，μg/m³；CO 为 mg/m³）。值越小越好。
const AIR = {
  aqi:  [[0, 100], [50, 90], [100, 75], [150, 55], [200, 35], [300, 15]],
  pm25: [[0, 100], [35, 85], [75, 70], [115, 50], [150, 35], [250, 15]],
  pm10: [[0, 100], [50, 85], [150, 70], [250, 50], [350, 35], [420, 15]],
  so2:  [[0, 100], [50, 85], [150, 70], [500, 40]],
  no2:  [[0, 100], [40, 85], [80, 70], [120, 55], [200, 40], [280, 20]],
  o3:   [[0, 100], [100, 85], [160, 70], [200, 55], [265, 40]],
  co:   [[0, 100], [2, 80], [4, 60], [8, 30]],
}

const DIM_META = [
  { key: 'air', name: '大气', color: '#3987e5' },
  { key: 'water', name: '水体', color: '#d95926' },
  { key: 'soil', name: '土壤', color: '#199e70' },
  { key: 'veg', name: '植被', color: '#c98500' },
  { key: 'eco', name: '生态', color: '#d55181' },
]

// 取每个维度的指标分数（返回 null 表示该指标无数据）
function indicatorScores(d) {
  const air = d.air || {}
  const water = d.water || {}
  const soil = d.soil || {}
  const idx = d.indices || {}
  const ndvi = d.ndvi?.mean
  const evi = idx.evi?.mean
  const wet = idx.wet?.mean
  const lst = idx.lst?.mean
  const ndbsi = idx.ndbsi?.mean
  const fvc = idx.fvc?.mean
  const lai = idx.lai?.mean
  const npp = d.npp?.mean

  // 大气：多污染物综合（缺失时退回 AQI）
  let airScores = [air.pm25, air.pm10, air.so2, air.no2, air.o3, air.co]
    .map((m, i) => lerp([AIR.pm25, AIR.pm10, AIR.so2, AIR.no2, AIR.o3, AIR.co][i], m?.mean))
    .filter((v) => v != null)
  if (!airScores.length && air.aqi?.mean != null) airScores = [lerp(AIR.aqi, air.aqi.mean)]

  return {
    air: airScores,
    water: [lerp([[ -0.1, 100], [0, 90], [0.02, 70], [0.1, 40], [0.3, 15]], water.fai?.median),
            lerp([[ 0, 100], [10, 90], [30, 75], [50, 55], [100, 30], [150, 15]], water.turbidity?.median)].filter((v) => v != null),
    soil: [clamp(100 - Math.abs((soil.ph?.mean ?? 7) - 7) * 18),
           lerp([[ 0, 40], [20, 70], [40, 90], [80, 100]], soil.som?.mean),
           clamp(soil.sqi?.mean)].filter((v) => v != null),
    veg: [lerp([[ -0.2, 20], [0, 40], [0.2, 55], [0.4, 70], [0.6, 85], [0.8, 100]], ndvi),
          lerp([[ -0.2, 20], [0, 40], [0.2, 55], [0.4, 70], [0.6, 85], [0.8, 100]], evi),
          lerp([[ 0, 10], [0.2, 30], [0.4, 55], [0.6, 75], [0.8, 90], [1, 100]], fvc),
          lerp([[ 0, 20], [1, 50], [2, 65], [3, 80], [5, 95]], lai),
          lerp([[ 0, 30], [300, 60], [600, 80], [900, 95], [1200, 100]], npp)].filter((v) => v != null),
    eco: [lerp([[ -0.2, 20], [0, 40], [0.2, 55], [0.4, 70], [0.6, 85], [0.8, 100]], ndvi), // 绿度 VI
          lerp([[ -1, 30], [-0.5, 45], [0, 60], [0.3, 85], [1, 100]], wet),               // 湿度 WET
          lerp([[ 15, 100], [25, 85], [35, 60], [40, 40], [45, 25], [50, 10]], lst),      // 热度 LST（越低越好）
          lerp([[ -0.5, 100], [-0.1, 85], [0, 60], [0.15, 40], [0.5, 15]], ndbsi)]        // 干度 NDBSI
           .filter((v) => v != null),
  }
}

const mean = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null)

// 近 12 期 NDVI 环比（用于大屏「较上月」），无时序则 null
function ndviDelta(d) {
  const ts = d.timeseries || []
  if (ts.length < 2) return null
  const last = ts[ts.length - 1].ndvi
  const prev = ts[ts.length - 2].ndvi
  if (last == null || prev == null) return null
  return +(last - prev).toFixed(4)
}

// 由真实遥感/监测数据构建五维评分、综合指数、达标率
export function buildScores(d) {
  if (!d) {
    return {
      isReal: false,
      dims: mockDims,
      comprehensive: mockComprehensive,
      compliance: mockCompliance,
      ndviDelta: null,
    }
  }
  const s = indicatorScores(d)
  const dims = DIM_META.map((m) => ({ ...m, score: Math.round(mean(s[m.key]) ?? 0) }))
  const comprehensive = +(mean(dims.map((x) => x.score)) ?? 0).toFixed(1)

  // 达标率 = 各维度内分数 ≥ 60 的指标占比
  const compliance = {
    names: DIM_META.map((m) => m.name),
    values: DIM_META.map((m) => {
      const sc = s[m.key]
      if (!sc.length) return 0
      return Math.round((sc.filter((v) => v >= 60).length / sc.length) * 100)
    }),
  }

  return { isReal: true, dims, comprehensive, compliance, ndviDelta: ndviDelta(d) }
}
