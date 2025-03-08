<script lang="ts" setup>
defineProps<{
  title: string;
  description: string;
  status: 'positive' | 'neutral' | 'negative';
}>();
</script>

<template>
  <div class="info-card">
    <div class="card-header">
      <h3>{{ title }}</h3>
      <span class="indicator" :class="status">{{ status === 'positive' ? '✓' : status === 'neutral' ? '!' : '×' }}</span>
    </div>
    <p>{{ description }}</p>
  </div>
</template>

<style scoped>
.info-card {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 0.875rem;
  text-align: left;
  border: 1px solid #3a3a3a;
  transition: transform 0.2s ease;
}

.info-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.info-card h3 {
  color: #54bc4a;
  font-size: 1rem;
  font-weight: bold;
  margin: 0;
}

.info-card p {
  color: #999;
  font-size: 0.875rem;
  line-height: 1.4;
  margin: 0;
}

.indicator {
  font-size: 0.875rem;
  font-weight: bold;
  padding: 0.2rem;
  border-radius: 50%;
}

.indicator.positive {
  color: #54bc4a;
}

.indicator.neutral {
  color: #f0ad4e;
}

.indicator.negative {
  color: #d9534f;
}
</style> 