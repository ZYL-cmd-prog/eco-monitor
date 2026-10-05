<script setup>
import { ref, onMounted, onBeforeUnmount, watch, shallowRef } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '320px' },
})

const el = ref(null)
const chart = shallowRef(null)
let observer = null

onMounted(() => {
  chart.value = echarts.init(el.value)
  chart.value.setOption(props.option)
  observer = new ResizeObserver(() => chart.value && chart.value.resize())
  observer.observe(el.value)
})

watch(
  () => props.option,
  (opt) => chart.value && chart.value.setOption(opt, true),
  { deep: true }
)

onBeforeUnmount(() => {
  observer && observer.disconnect()
  chart.value && chart.value.dispose()
})
</script>

<template>
  <div ref="el" :style="{ width: '100%', height }"></div>
</template>
