// 五维指标类别（颜色对应全局 CSS 变量，用于图表系列）
export const dimensions = [
  { key: 'air', name: '大气', score: 82, delta: '+2.1%', color: '#3987e5' },
  { key: 'water', name: '水体', score: 76, delta: '+1.4%', color: '#d95926' },
  { key: 'soil', name: '土壤', score: 74, delta: '+0.8%', color: '#199e70' },
  { key: 'veg', name: '植被', score: 88, delta: '+3.2%', color: '#c98500' },
  { key: 'eco', name: '生态', score: 80, delta: '+1.9%', color: '#d55181' },
]

// 综合生态环境质量指数（0-100）
export const comprehensiveScore = 82.6

// 20 项指标（五维 × 4）
export const indicators = [
  // 大气
  { code: 'SO2', name: '二氧化硫', category: '大气', value: 8, unit: 'μg/m³', level: '优', trend: -1 },
  { code: 'NO2', name: '二氧化氮', category: '大气', value: 28, unit: 'μg/m³', level: '优', trend: -1 },
  { code: 'O3', name: '臭氧', category: '大气', value: 96, unit: 'μg/m³', level: '良', trend: 0 },
  { code: 'AQI', name: '空气质量指数', category: '大气', value: 65, unit: '', level: '良', trend: -1 },
  // 水体
  { code: 'WQI', name: '水质指数', category: '水体', value: 78, unit: '', level: '良好', trend: 1 },
  { code: 'FAI', name: '浮游藻类指数', category: '水体', value: 0.12, unit: '', level: '正常', trend: 0 },
  { code: 'CMI', name: '大型藻类指数', category: '水体', value: 0.08, unit: '', level: '正常', trend: 0 },
  { code: 'RGBT', name: '红绿蓝浑浊度', category: '水体', value: 15, unit: 'NTU', level: '良好', trend: -1 },
  // 土壤
  { code: 'SQI', name: '土壤质量指数', category: '土壤', value: 72, unit: '', level: '良好', trend: 1 },
  { code: 'PH', name: '土壤酸碱度', category: '土壤', value: 6.8, unit: '', level: '中性', trend: 0 },
  { code: 'SOM', name: '土壤有机质', category: '土壤', value: 21, unit: 'g/kg', level: '良好', trend: 1 },
  { code: 'HM', name: '土壤重金属指数', category: '土壤', value: 0.35, unit: '', level: '安全', trend: 0 },
  // 植被
  { code: 'EVI', name: '增强植被指数', category: '植被', value: 0.42, unit: '', level: '正常', trend: 1 },
  { code: 'FVC', name: '植被覆盖度', category: '植被', value: 0.62, unit: '', level: '良好', trend: 1 },
  { code: 'LAI', name: '叶面积指数', category: '植被', value: 2.8, unit: '', level: '良好', trend: 1 },
  { code: 'NPP', name: '净初级生产力', category: '植被', value: 480, unit: 'gC/m²·a', level: '良好', trend: 1 },
  // 生态
  { code: 'VI', name: '绿度', category: '生态', value: 0.55, unit: '', level: '良好', trend: 1 },
  { code: 'WET', name: '湿度', category: '生态', value: 0.38, unit: '', level: '正常', trend: 0 },
  { code: 'LST', name: '热度', category: '生态', value: 24.5, unit: '°C', level: '正常', trend: 0 },
  { code: 'NDBSI', name: '干度', category: '生态', value: 0.12, unit: '', level: '优', trend: -1 },
]

// 近 12 个月趋势（0-100 指数）
export const trend = {
  months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  series: [
    { name: '综合质量指数', data: [72, 73, 74, 75, 74, 76, 78, 77, 79, 80, 81, 82] },
    { name: '大气质量指数', data: [68, 70, 71, 73, 72, 75, 77, 76, 78, 80, 81, 82] },
    { name: '水体质量指数', data: [70, 71, 72, 73, 74, 75, 76, 76, 77, 78, 79, 79] },
  ],
}

// 各维度指标达标率（%）
export const compliance = {
  names: ['大气', '水体', '土壤', '植被', '生态'],
  values: [85, 78, 74, 92, 81],
}

// Transformer 预测（历史 12 期 + 未来 12 期）
export const prediction = {
  labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月',
    '预测1', '预测2', '预测3', '预测4', '预测5', '预测6', '预测7', '预测8', '预测9', '预测10', '预测11', '预测12'],
  history: [72, 73, 74, 75, 74, 76, 78, 77, 79, 80, 81, 82],
  future: [83, 84, 85, 86, 85, 87, 88, 87, 89, 90, 91, 92],
  upper: [null, null, null, null, null, null, null, null, null, null, null, null, 85, 86, 87, 88, 87, 89, 90, 89, 91, 92, 93, 94],
  lower: [null, null, null, null, null, null, null, null, null, null, null, null, 81, 82, 83, 84, 83, 85, 86, 85, 87, 88, 89, 90],
}

// 相关性矩阵（8 个指标，-1 ~ 1）
export const correlation = {
  names: ['AQI', 'SO2', 'NO2', 'WQI', 'SQI', 'EVI', 'FVC', 'LST'],
  matrix: [
    [1.00, 0.72, 0.68, -0.35, -0.18, -0.42, -0.38, 0.41],
    [0.72, 1.00, 0.61, -0.28, -0.12, -0.35, -0.31, 0.33],
    [0.68, 0.61, 1.00, -0.30, -0.15, -0.40, -0.36, 0.38],
    [-0.35, -0.28, -0.30, 1.00, 0.52, 0.48, 0.45, -0.22],
    [-0.18, -0.12, -0.15, 0.52, 1.00, 0.58, 0.55, -0.10],
    [-0.42, -0.35, -0.40, 0.48, 0.58, 1.00, 0.82, -0.35],
    [-0.38, -0.31, -0.36, 0.45, 0.55, 0.82, 1.00, -0.32],
    [0.41, 0.33, 0.38, -0.22, -0.10, -0.35, -0.32, 1.00],
  ],
}

// 污染溯源
export const tracing = [
  { source: '工业点源', contribution: 38 },
  { source: '农业面源', contribution: 27 },
  { source: '交通尾气', contribution: 19 },
  { source: '生活源', contribution: 11 },
  { source: '其他', contribution: 5 },
]

// 监测站点（长江上游）
export const stations = [
  { name: '宜宾站', lon: 104.62, lat: 28.75, type: '大气站', value: 65 },
  { name: '泸州站', lon: 105.44, lat: 28.87, type: '水质站', value: 72 },
  { name: '重庆站', lon: 106.55, lat: 29.56, type: '大气站', value: 58 },
  { name: '成都站', lon: 104.07, lat: 30.57, type: '生态站', value: 80 },
  { name: '乐山站', lon: 103.76, lat: 29.55, type: '水质站', value: 76 },
  { name: '攀枝花站', lon: 101.72, lat: 26.58, type: '生态站', value: 84 },
  { name: '昭通站', lon: 103.72, lat: 27.34, type: '土壤站', value: 70 },
  { name: '遵义站', lon: 106.93, lat: 27.73, type: '大气站', value: 62 },
  { name: '贵阳站', lon: 106.63, lat: 26.65, type: '土壤站', value: 74 },
  { name: '昆明站', lon: 102.83, lat: 24.88, type: '生态站', value: 82 },
]

// 预警事件
export const alerts = [
  { time: '2025-11-04 08:20', area: '宜宾城区', type: '大气污染', level: '红色', status: '处理中', desc: 'PM2.5 连续 3 小时超标，启动应急响应' },
  { time: '2025-11-03 16:45', area: '泸州沱江支流', type: '水体富营养化', level: '橙色', status: '处理中', desc: '叶绿素 a 浓度异常升高' },
  { time: '2025-11-03 10:12', area: '重庆某工业园区', type: '土壤重金属', level: '黄色', status: '待处理', desc: '镉含量接近风险阈值' },
  { time: '2025-11-02 09:30', area: '攀枝花干热河谷', type: '植被退化', level: '蓝色', status: '已处理', desc: 'NDVI 连续下降，建议生态修复' },
  { time: '2025-11-01 22:05', area: '成都近郊', type: '水质异常', level: '红色', status: '处理中', desc: '氨氮浓度超标，疑似点源偷排' },
  { time: '2025-10-31 14:40', area: '遵义城区', type: '大气污染', level: '橙色', status: '已处理', desc: 'O3 午后峰值超标' },
  { time: '2025-10-30 11:20', area: '昭通高寒山区', type: '生态退化', level: '黄色', status: '待处理', desc: '湿地面积缩减' },
  { time: '2025-10-29 15:00', area: '乐山农田区', type: '土壤面源', level: '蓝色', status: '已处理', desc: '化肥施用强度偏高' },
]
