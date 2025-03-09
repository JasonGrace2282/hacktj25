<script lang="ts" setup>
defineProps<{
    credibility: number;
    dataPoints?: number;
    biasStrengths?: number[];
    showDebug?: boolean;
}>();

const getColor = (score: number) => {
  if (score >= 70) return '#54bc4a';
  if (score >= 40) return '#f0ad4e';
  return '#d9534f';
};
</script>

<template>
  <div class="circle-container">
    <div class="circle" :style="{ borderColor: getColor(credibility) }">
      <span class="credibility" :style="{ color: getColor(credibility) }">{{ credibility }}%</span>
      <span class="label" :style="{ color: getColor(credibility) }">Credibility</span>
    </div>
    
    <div v-if="showDebug && biasStrengths && biasStrengths.length > 0" class="debug-info">
      <p>Raw bias strengths:</p>
      <ul>
        <li v-for="(strength, index) in biasStrengths" :key="index">
          {{ strength.toFixed(4) }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.circle-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.circle {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: #333333;
  border: 8px solid;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
  gap: 0rem;
  transition: all 0.3s ease;
}

.label {
  font-size: 1rem;
  font-weight: 500;
  transition: color 0.3s ease;
}

.credibility {
  font-size: 3rem;
  font-weight: bold;
  transition: color 0.3s ease;
}

.data-points {
  font-size: 0.75rem;
  color: #aaa;
  margin-top: 0.25rem;
}

.debug-info {
  margin-top: 1rem;
  font-size: 0.75rem;
  color: #999;
  text-align: left;
  background: #222;
  padding: 0.5rem;
  border-radius: 4px;
  max-height: 150px;
  overflow-y: auto;
  width: 90%;
}

.debug-info p {
  margin: 0 0 0.25rem 0;
}

.debug-info ul {
  margin: 0;
  padding-left: 1rem;
}

.debug-info li {
  margin-bottom: 0.125rem;
}
</style> 