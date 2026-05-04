<script setup>
import { ref, watch, onUnmounted } from 'vue'
import api from '../api'

const props = defineProps(['jobId'])

const stages = ref([])
const activeStages = ref([])
const activePollingStage = ref(null)
let interval = null

const fetchStages = async () => {
  const res = await api.get(`jobs/${props.jobId}/stages/`)
  stages.value = res.data
}

fetchStages()

const toggleStage = (id) => {
  if (activeStages.value.includes(id)) {
    activeStages.value = activeStages.value.filter(s => s !== id)

    if (activePollingStage.value === id) {
      activePollingStage.value = null
    }
  } else {
    activeStages.value.push(id)
    activePollingStage.value = id
  }
}

watch(activePollingStage, (newId) => {
  if (interval) clearInterval(interval)

  if (!newId) return

  interval = setInterval(async () => {
    const res = await api.get(`jobs/${props.jobId}/stages/`)
    const updated = res.data.find(s => s.id === newId)

    if (!updated) return

    const index = stages.value.findIndex(s => s.id === newId)
    if (index !== -1) {
      stages.value[index] = updated
    }

    if (['done', 'failed'].includes(updated.status)) {
      clearInterval(interval)
      activePollingStage.value = null
    }
  }, 3000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})

const statusClass = (status) => {
  return {
    pending: 'gray',
    running: 'orange',
    done: 'green',
    failed: 'red'
  }[status] || 'gray'
}

const logClass = (level) => {
  return {
    info: 'log-info',
    warning: 'log-warning',
    error: 'log-error'
  }[level] || 'log-info'
}
</script>

<template>
  <div class="stages">
    <div v-for="stage in stages" :key="stage.id" class="stage">

      <div class="stage-header" @click="toggleStage(stage.id)">
        <div>
          <span class="arrow">
            {{ activeStages.includes(stage.id) ? '▼' : '▶' }}
          </span>
          {{ stage.name }}
        </div>

        <span :class="['status', statusClass(stage.status)]">
          {{ stage.status }}
        </span>
      </div>

      <div v-if="activeStages.includes(stage.id)" class="logs">
        <div 
          v-for="log in stage.logs" 
          :key="log.id" 
          :class="['log', logClass(log.level)]"
        >
          {{ log.message }}
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.stages {
  margin-top: 12px;
  padding-left: 10px;
}

.stage {
  border-left: 2px solid #ddd;
  padding-left: 10px;
  margin-bottom: 10px;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  cursor: pointer;
  font-weight: 500;
}

.arrow {
  margin-right: 6px;
}

.status {
  font-size: 12px;
}

.gray { color: gray; }
.orange { color: orange; }
.green { color: green; }
.red { color: red; }

.logs {
  margin-top: 8px;
  font-size: 13px;
}

.log {
  padding: 4px 0;
}

.log-info { color: #333; }
.log-warning { color: orange; }
.log-error { color: red; font-weight: bold; }
</style>