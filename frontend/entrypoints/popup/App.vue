<script lang="ts" setup>

import CredibilityScore from '@/components/CredibilityScore.vue';
import InfoCard from '@/components/InfoCard.vue';
import { ref, onMounted, onUnmounted, watch } from 'vue';

const credibility = ref(30);
const currentWebsite = ref('');
const websocket = ref<WebSocket | null>(null);

const cardData = [
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
];

const connectWebSocket = (url: string) => {
  if (websocket.value) {
    console.log('Closing existing WebSocket connection');
    websocket.value.close();
  }

  const encodedUrl = encodeURIComponent(url);
  const wsUrl = `ws://localhost:8080/ws/thingy/credibility/${encodedUrl}`;
  console.log('Attempting to connect to WebSocket:', wsUrl);
  
  websocket.value = new WebSocket(wsUrl);

  websocket.value.onopen = () => {
    console.log('WebSocket connection established successfully');
  };

  websocket.value.onmessage = (event) => {
    console.log('WebSocket message received:', event.data);
    try {
      const data = JSON.parse(event.data);
      console.log('Parsed WebSocket data:', data);
      if (data.bias_strength !== undefined) {
        credibility.value = Math.round((1 - data.bias_strength) * 100);
        console.log('Updated credibility score:', credibility.value);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  websocket.value.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  websocket.value.onclose = (event) => {
    console.log('WebSocket disconnected:', event.code, event.reason);
    websocket.value = null;
  };
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
      connectWebSocket(parsedUrl);

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

// Cleanup WebSocket connection when component is unmounted
onUnmounted(() => {
  if (websocket.value) {
    websocket.value.close();
  }
});

const waitForElement = (selector: string, timeout = 5000) => {
    return new Promise<HTMLElement | null>((resolve) => {
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

</script>

<template>
  <div class="app-container">
    <div class="content">
      <CredibilityScore :credibility="credibility" />
      <p class="interpretation">
        {{ credibility.value >= 70 ? 'This source appears to be highly credible.' :
           credibility.value >= 40 ? 'This source has moderate credibility.' :
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
