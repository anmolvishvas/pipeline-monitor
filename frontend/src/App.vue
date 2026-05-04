<script setup lang="ts">

import { provide, ref } from 'vue'
import JobList from './components/JobList.vue'

const role = ref('operator') 

provide('role', role)
</script>

<template>
  <JobList />
</template>
