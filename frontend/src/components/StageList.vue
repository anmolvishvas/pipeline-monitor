<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'
import api from '../api'

const props = defineProps(['jobId'])

const stages = ref([])
const activeStageId = ref(null)

const stopFn = ref(null)

const stageErrors = ref({})
const stageFlash = ref({})

const fetchStages = async () => {
  const res = await api.get(`jobs/${props.jobId}/stages/`)
  stages.value = res.data
}

fetchStages()

const toggleStage = (id) => {
  activeStageId.value = activeStageId.value === id ? null : id
}

watch(activeStageId, async (newId) => {
  if (stopFn.value) {
    stopFn.value()
    stopFn.value = null
  }

  if (!newId) return

  let interval = null
  let cancelled = false

  const poll = async () => {
    if (cancelled) return

    const res = await api.get(`jobs/${props.jobId}/stages/`)
    const updated = res.data.find(s => s.id === newId)

    if (!updated) return

    const index = stages.value.findIndex(s => s.id === newId)
    const prevLogs = stages.value[index]?.logs || []

    if (updated.status !== 'running') {
      clearInterval(interval)
      cancelled = true
    }

    const existingIds = new Set(prevLogs.map(l => l.id))
    const newLogs = updated.logs.filter(l => !existingIds.has(l.id))

    const container = document.getElementById(`logs-${newId}`)
    const scrollTop = container?.scrollTop

    stages.value[index] = {
      ...updated,
      logs: [...prevLogs, ...newLogs]
    }

    if (newLogs.some(l => l.level === 'error')) {
      stageErrors.value[newId] = 'Error detected in stage!'

      stageFlash.value[newId] = true
      setTimeout(() => {
        stageFlash.value[newId] = false
      }, 800)
    }

    await nextTick()

    if (container) {
      container.scrollTop = scrollTop
    }
  }

  interval = setInterval(poll, 5000)

  stopFn.value = () => {
    cancelled = true
    clearInterval(interval)
  }

})

onUnmounted(() => {
  if (stopFn.value) stopFn.value()
})

const statusClass = (status) => {
  return {
    pending: 'gray',
    running: 'orange',
    done: 'green',
    failed: 'red'
  }[status] || 'gray'
}
</script>

<template>
  <div class="stages">

    <div v-for="stage in stages" :key="stage.id" class="stage">

      <div class="stage-header" @click="toggleStage(stage.id)">
        <div>
          <span>
            {{ activeStageId === stage.id ? '▼' : '▶' }}
          </span>
          {{ stage.name }}
        </div>

        <span 
          :class="[
            'status',
            statusClass(stage.status),
            stageFlash[stage.id] ? 'flash' : ''
          ]"
        >
          {{ stage.status }}
        </span>
      </div>

      <div v-if="stageErrors[stage.id]" class="alert">
        ⚠ {{ stageErrors[stage.id] }}
        <button @click="stageErrors[stage.id] = null">✖</button>
      </div>

      <div 
        v-if="activeStageId === stage.id"
        class="logs"
        :id="'logs-' + stage.id"
      >
        <div 
          v-for="log in stage.logs"
          :key="log.id"
          class="log"
          :class="{ error: log.level === 'error' }"
        >
          {{ log.message }}
        </div>
      </div>

    </div>

  </div>
</template>

<style scoped>
.stage {
  border-left: 2px solid #ddd;
  padding-left: 10px;
  margin-bottom: 12px;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  cursor: pointer;
}

.logs {
  max-height: 150px;
  overflow-y: auto;
  margin-top: 8px;
}

.log {
  padding: 4px;
}

.log.error {
  color: red;
  font-weight: bold;
}

.alert {
  background: #ffe0e0;
  color: red;
  padding: 6px;
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
}

.gray { color: gray }
.orange { color: orange }
.green { color: green }
.red { color: red }

.flash {
  animation: blink 0.6s ease;
}

@keyframes blink {
  0% { opacity: 1 }
  50% { opacity: 0.2 }
  100% { opacity: 1 }
}
</style>