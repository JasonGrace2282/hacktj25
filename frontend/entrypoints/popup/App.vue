<script lang="ts" setup>

import CredibilityScore from '@/components/CredibilityScore.vue';
import InfoCard from '@/components/InfoCard.vue';
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';

const credibility = ref(30);
const currentWebsite = ref('');
const currentUrl = ref('');
const biasStrengths = ref<number[]>([]);
const isLoading = ref(false);

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
    title: 'Fact Checking',
    description: 'Multiple reliable sources verify the information presented on this site.',
    status: 'positive' as const,
    credibilityScore: credibility.value
  },
  {
    title: 'Source History',
    description: 'This source has a track record of accurate reporting and transparency.',
    status: 'positive' as const,
    credibilityScore: credibility.value
  }
]);

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
      
      // Create the BiasedMedia object
      try {
        const createResponse = await fetch(`http://localhost:8080/api/biased-media/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            url: parsedUrl,
            title: currentWebsite.value,
            source_type: parsedUrl.includes('tiktok.com') ? 'tiktok' : 'website'
          }),
        });
        
        if (createResponse.ok) {
          console.log('Successfully created BiasedMedia object on startup');
          
          // After creating the BiasedMedia object, fetch credibility data
          await fetchCredibilityData(parsedUrl);
        } else {
          console.warn('Could not create BiasedMedia object on startup, status:', createResponse.status);
          
          // Try to fetch credibility data anyway, as the object might already exist
          await fetchCredibilityData(parsedUrl);
        }
      } catch (createError) {
        console.error('Error creating BiasedMedia object on startup:', createError);
        
        // Try to fetch credibility data anyway
        await fetchCredibilityData(parsedUrl);
      }

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
      />
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
        <button class="debug-toggle" @click="showDebug = !showDebug">
          {{ showDebug ? 'Hide Debug' : 'Show Debug' }}
        </button>
      </div>
      
      <div v-if="isLoading" class="loading-indicator">
        Loading credibility data...
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

.loading-indicator {
  color: #666;
  font-size: 0.75rem;
  padding: 0.5rem;
  font-style: italic;
}
</style>