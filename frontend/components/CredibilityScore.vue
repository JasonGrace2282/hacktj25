<script lang="ts" setup>
defineProps<{
    credibility: number;
}>();
</script>

<template>
  <div class="circle-container">
    <div class="circle">
      <span class="credibility">{{ credibility }}%</span>
    </div>
  </div>
</template>

<style scoped>
.circle-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.circle {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: #333333;
  border: 8px solid #54bc4a;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 0 15px rgba(84, 188, 74, 0.3);
}

.credibility {
  font-size: 3rem;
  font-weight: bold;
  color: #54bc4a;
}
</style> 