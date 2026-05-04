<script setup>
import { ref, onMounted, onUnmounted, inject, computed } from 'vue'
import api from '../api'
import StageList from './StageList.vue'

let interval = null

const jobs = ref([])
const expandedJob = ref(null)
const role = inject('role', ref('viewer'))

const statusFilter = ref('all')
const errorFilter = ref(false)

const jobErrors = ref({})

const fetchJobs = async () => {
  const res = await api.get('jobs/')
  jobs.value = res.data
}

onMounted(() => {
  fetchJobs()
  interval = setInterval(fetchJobs, 5000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})

const filteredJobs = computed(() => {
  return jobs.value.filter(job => {
    const statusMatch =
      statusFilter.value === 'all' ||
      job.status === statusFilter.value

    const errorMatch =
      !errorFilter.value ||
      job.error_count > 0

    return statusMatch && errorMatch
  })
})

const triggerJob = async (job) => {
  jobErrors.value[job.id] = null

  const prevStatus = job.status

  job.status = 'running'

  try {
    await api.post(`jobs/${job.id}/trigger/`)
    await fetchJobs()
  } catch (e) {
    job.status = prevStatus

    jobErrors.value[job.id] =
      e?.response?.data?.error || 'Failed to trigger job'
  }
}

const statusClass = (status) => {
  return {
    queued: 'badge-gray',
    running: 'badge-orange',
    completed: 'badge-green',
    failed: 'badge-red'
  }[status] || 'badge-gray'
}
</script>

<template>
  <div class="container">
    <h1 class="title">Pipeline Monitor</h1>

    <div class="filter-bar">
      <select v-model="statusFilter">
        <option value="all">All</option>
        <option value="queued">Queued</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>

      <label>
        <input type="checkbox" v-model="errorFilter" />
        Only errors
      </label>
    </div>

    <div v-if="filteredJobs.length === 0" class="empty">
      No jobs available
    </div>

    <div v-for="job in filteredJobs" :key="job.id" class="job-card">
      <div class="job-header">
        <div class="job-title">
          <h3>{{ job.name }}</h3>

          <span v-if="job.retry_count > 0" class="retry-badge">
            Retried {{ job.retry_count }}×
          </span>

          <span :class="['badge', statusClass(job.status)]">
            {{ job.status }}
          </span>
        </div>

        <div class="actions">

          <button 
            v-if="role === 'operator' && (job.status === 'queued' || job.status === 'failed')"
            class="btn primary"
            @click="triggerJob(job)"
          >
            ▶ {{ job.status === 'failed' ? 'Retry' : 'Trigger' }}
          </button>

          <button 
            class="btn secondary"
            @click="expandedJob = expandedJob === job.id ? null : job.id"
          >
            {{ expandedJob === job.id ? 'Hide' : 'View Stages' }}
          </button>

        </div>
      </div>

      <div v-if="jobErrors[job.id]" class="error-msg">
        ⚠ {{ jobErrors[job.id] }}
      </div>

      <StageList 
        v-if="expandedJob === job.id"
        :jobId="job.id"
      />
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Arial, sans-serif;
}

.title {
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.job-card {
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fff;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.job-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
}

.primary {
  background: #007bff;
  color: white;
}

.secondary {
  background: #eee;
}

.badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
}

.badge-gray { background: #ccc; }
.badge-orange { background: orange; color: white; }
.badge-green { background: green; color: white; }
.badge-red { background: red; color: white; }

.retry-badge {
  background: purple;
  color: white;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.error-msg {
  color: red;
  font-size: 13px;
  margin-top: 6px;
}

.empty {
  text-align: center;
  color: #888;
}
</style>