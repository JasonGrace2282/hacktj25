<script lang="ts" setup>

import CredibilityScore from '@/components/CredibilityScore.vue';
import InfoCard from '@/components/InfoCard.vue';
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';

const credibility = ref<number | null>(null);
const currentWebsite = ref('');
const currentUrl = ref('');
const biasStrengths = ref<number[]>([]);
const isLoading = ref(false);
const contents = ref<any[]>([]);

// Function to fetch credibility data from the API
const fetchCredibilityData = async (url: string) => {
  try {
    isLoading.value = true;
    console.log('Fetching credibility data for:', url);
    
    // Encode the URL for use in the API endpoint
    const encodedUrl = encodeURIComponent(url);
    const response = await fetch(`http://localhost:8080/credibility/${encodedUrl}`, {
      method: 'POST',
    });
    
    const data = await response.json();
    console.log('Received credibility data:', data);
    
    const biasStrength = data.average_bias;
    console.log(data.contents)
    
    // Sort contents by bias_strength in descending order
    contents.value = data.contents.sort((a: any, b: any) => b.bias_strength - a.bias_strength).filter((content: any) => content.bias_strength > 0);
    console.log('Sorted contents:', contents.value);
    
    console.log('Found bias strength:', biasStrength);
    
    // Round to 2 decimal places to ensure maximum 4 digits (e.g., 99.99)
    credibility.value = Number(biasStrength.toFixed(2)) * 100;
    console.log('Updated credibility score:', credibility.value);
  } catch (error) {
    console.error('Error fetching credibility data:', error);
  } finally {
    isLoading.value = false;
  }
};

// Card data with computed property to ensure reactivity
const cardData = computed(() => [
  {
    title: 'Biased Statements',
    status: 'positive' as const,
    credibilityScore: credibility.value ?? 0,
    showContents: true, // Flag to indicate this card should show contents
    isFactChecking: true, // Flag to identify this as the Fact Checking card
    description: 'Potentially biased content detected in this article'
  },
]);

// Get the top two contents sorted by bias_strength
const topContents = computed(() => {
  return contents.value.slice(0, 2);
});

const waitForElement = (selector: string, timeout = 5000) => {
  return new Promise<Element | null>((resolve) => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const element = document.querySelector(selector);
      if (element) {
        clearInterval(interval);
        resolve(element);
      }
      if (Date.now() - startTime > timeout) {
        clearInterval(interval);
        resolve(null); // Timeout
      }
    }, 500); // Check every 500ms
  });
};

onMounted(async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (tab?.url) {
      const url = new URL(tab.url);
      let parsedUrl = tab.url;

      if (url.hostname.includes('tiktok.com')) {
        let username;
        if (url.href.includes("tiktok.com/foryou") || url.href.includes("tiktok.com/en")) {
          username = await waitForElement('[data-e2e="video-author-uniqueid"]');
          let videoId = await waitForElement(".tiktok-web-player");
          let id;

          if (username) username = username.textContent;
          if (videoId) id = videoId.id;

          if (id) {
            id = id.substring(id.indexOf("-0-") + 3);
          }

          parsedUrl = `https://www.tiktok.com/@${username}/video/${id}`;
        } else {
          const pathParts = url.pathname.split('/');
          username = pathParts.find(part => part.startsWith('@'));
        }
        currentWebsite.value = username || 'Unknown TikTok user';
      } else {
        currentWebsite.value = url.hostname;
      }
      
      currentUrl.value = parsedUrl;

      await fetchCredibilityData(parsedUrl);

      if (tab.id) {
        chrome.tabs.sendMessage(tab.id, { 
          type: 'credibilityUpdate',
          credibility: credibility.value 
        });
      }
    }
  } catch (error) {
    console.error('Error getting current tab:', error);
    currentWebsite.value = 'Unknown website';
  }
});

// Watch for credibility changes and update content script
watch(credibility, async (newValue) => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.id) {
      chrome.tabs.sendMessage(tab.id, {
        type: 'credibilityUpdate',
        credibility: newValue
      });
    }
  } catch (error) {
    console.error('Error sending credibility update:', error);
  }
});

const showDebug = ref(false);
</script>

<template>
  <div class="app-container">
    <div class="content">
      <CredibilityScore 
        :credibility="credibility" 
        :data-points="biasStrengths.length" 
        :bias-strengths="biasStrengths"
        :show-debug="showDebug"
        :is-loading="isLoading"
      />
      <p class="interpretation" v-if="!isLoading && credibility !== null">
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
          :contents="card.isFactChecking ? topContents : []"
          :show-contents="card.showContents"
        />
      </div>
      
      <div class="website-name">
        {{ currentWebsite }}
        <button class="debug-toggle" @click="showDebug = !showDebug">
          {{ showDebug ? 'Hide Debug' : 'Show Debug' }}
        </button>
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

.debug-toggle {
  background: none;
  border: none;
  color: #999;
  font-size: 0.7rem;
  cursor: pointer;
  margin-left: 0.5rem;
  text-decoration: underline;
  padding: 0;
}

.debug-toggle:hover {
  color: #ccc;
}
</style>
