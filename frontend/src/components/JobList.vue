<script setup>
import { ref, onMounted, inject } from 'vue'
import api from '../api'
import StageList from './StageList.vue'

const jobs = ref([])
const expandedJob = ref(null)
const role = inject('role')

const fetchJobs = async () => {
  const res = await api.get('jobs/')
  jobs.value = res.data
}

onMounted(fetchJobs)

const triggerJob = async (job) => {
  const oldStatus = job.status
  job.status = 'running'
  try {
    await api.post(`jobs/${job.id}/trigger/`)
  } catch (e) {
    job.status = oldStatus
    alert("Trigger failed")
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

    <div v-if="jobs.length === 0" class="empty">
      No jobs available
    </div>

    <div v-for="job in jobs" :key="job.id" class="job-card">
      <div class="job-header">
        <div>
          <h3>{{ job.name }}</h3>
          <span :class="['badge', statusClass(job.status)]">
            {{ job.status }}
          </span>
        </div>

        <div class="actions">
          <button 
            v-if="role === 'operator' && job.status === 'queued'"
            class="btn primary"
            @click="triggerJob(job)"
          >
            ▶ Trigger
          </button>

          <button 
            class="btn secondary"
            @click="expandedJob = expandedJob === job.id ? null : job.id"
          >
            {{ expandedJob === job.id ? 'Hide' : 'View Stages' }}
          </button>
        </div>
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
  display: inline-block;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  margin-top: 4px;
}

.badge-gray { background: #ccc; }
.badge-orange { background: orange; color: white; }
.badge-green { background: green; color: white; }
.badge-red { background: red; color: white; }

.empty {
  text-align: center;
  color: #888;
}
</style>