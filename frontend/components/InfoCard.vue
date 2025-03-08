<script lang="ts" setup>
defineProps<{
  title: string;
  description: string;
  status: 'positive' | 'neutral' | 'negative';
  credibilityScore: number;
}>();

const getColor = (score: number) => {
  if (score >= 70) return '#54bc4a';
  if (score >= 40) return '#f0ad4e';
  return '#d9534f';
};
</script>

<template>
  <div class="info-card" :style="{ borderColor: getColor(credibilityScore) }">
    <div class="card-content">
      <div class="card-header">
        <h3 :style="{ color: getColor(credibilityScore) }">{{ title }}</h3>
        <span class="indicator" :class="status" :style="{ color: getColor(credibilityScore) }">
          {{ status === 'positive' ? '✓' : status === 'neutral' ? '!' : '×' }}
        </span>
      </div>
      <p>{{ description }}</p>
    </div>
  </div>
</template>

<style scoped>
.info-card {
  background: #2a2a2a;
  border-radius: 8px;
  text-align: left;
  border: 1px solid;
  position: relative;
  transition: all 0.3s ease;
}

.card-content {
  padding: 0.875rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.info-card h3 {
  font-size: 1rem;
  font-weight: bold;
  margin: 0;
  transition: color 0.3s ease;
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
  transition: color 0.3s ease;
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