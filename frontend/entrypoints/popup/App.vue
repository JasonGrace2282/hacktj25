<script lang="ts" setup>

import CredibilityScore from '@/components/CredibilityScore.vue';
import InfoCard from '@/components/InfoCard.vue';
import { ref, onMounted } from 'vue';

const credibility = 30;
const currentWebsite = ref('');

const cardData = [
  {
    title: 'Fact Checking',
    description: 'Multiple reliable sources verify the information presented on this site.',
    status: 'positive' as const,
    credibilityScore: credibility
  },
  {
    title: 'Source History',
    description: 'This source has a track record of accurate reporting and transparency.',
    status: 'positive' as const,
    credibilityScore: credibility
  }
];

onMounted(async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.url) {
      const url = new URL(tab.url);
      if (url.hostname.includes('tiktok.com')) {
        const pathParts = url.pathname.split('/');
        const username = pathParts.find(part => part.startsWith('@'));
        currentWebsite.value = username || 'Unknown TikTok user';
      } else {
        currentWebsite.value = url.hostname;
      }
    }
  } catch (error) {
    console.error('Error getting current tab:', error);
    currentWebsite.value = 'Unknown website';
  }
});
</script>

<template>
  <div class="app-container">
    <div class="content">
      <CredibilityScore :credibility="credibility" />
      <p class="interpretation">
        {{ credibility >= 70 ? 'This source appears to be highly credible.' :
           credibility >= 40 ? 'This source has moderate credibility.' :
           'This source may have credibility concerns.' }}
      </p>

      <div class="cards-container">
        <InfoCard
          v-for="card in cardData"
          :key="card.title"
          :title="card.title"
          :description="card.description"
          :status="card.status"
          :credibility-score="card.credibilityScore"
        />
      </div>
      
      <div class="website-name">
        {{ currentWebsite }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  min-width: 350px;
  min-height: 180px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 0;
}

.content {
  text-align: center;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  padding-top: 0.25rem;
}

.interpretation {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
  padding: 1rem;
}

.cards-container {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  padding: 0;
  margin: 0 0.25rem;
  margin-top: 0.25rem;
}

.website-name {
  color: #666;
  font-size: 0.75rem;
  padding: 0.5rem;
  margin-top: 0.25rem;
  border-top: 1px solid #3a3a3a;
}
</style>
