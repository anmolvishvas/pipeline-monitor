<script setup>
import { ref, provide, onMounted } from 'vue'
import api from './api'
import JobList from './components/JobList.vue'

const role = ref('viewer')

onMounted(async () => {
  try {
    const res = await api.get('me/')
    role.value = res.data.role
  } catch {
    role.value = 'viewer'
  }
})

provide('role', role)
</script>

<template>
  <div>
    <div v-if="loading" class="loading">
      Loading...
    </div>

    <JobList v-else />
  </div>
</template>

<style scoped>
.loading {
  text-align: center;
  margin-top: 100px;
  font-size: 18px;
  color: #555;
}
</style>