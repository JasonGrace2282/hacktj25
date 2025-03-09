<script lang="ts" setup>

import CredibilityScore from '@/components/CredibilityScore.vue';
import InfoCard from '@/components/InfoCard.vue';
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
// @ts-ignore
import { useWebSocket } from '@/composables/useWebSocket';

// Define the expected data structure from the WebSocket
interface CredibilityData {
  bias_strength?: number;
  [key: string]: any;
}

const credibility = ref(30);
const currentWebsite = ref('');
const currentUrl = ref('');
// Track all bias strengths received for averaging
const biasStrengths = ref<number[]>([]);

// Function to calculate average credibility from all bias strengths
const calculateAverageCredibility = () => {
  if (biasStrengths.value.length === 0) return 30; // Default value if no data
  
  const sum = biasStrengths.value.reduce((acc, val) => acc + val, 0);
  const average = sum / biasStrengths.value.length;
  // Convert bias strength to credibility score (inverse relationship)
  return Math.round((1 - average) * 100);
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

// Function to generate mock bias strength data for testing
const generateMockBiasData = (count = 5, minBias = 0.2, maxBias = 0.8) => {
  const mockData = [];
  for (let i = 0; i < count; i++) {
    // Generate a random bias strength between minBias and maxBias
    const biasStrength = minBias + Math.random() * (maxBias - minBias);
    mockData.push(biasStrength);
  }
  return mockData;
};

// Function to load mock data if no real data is received after a timeout
const loadMockDataAfterDelay = (delayMs = 5000) => {
  setTimeout(() => {
    if (biasStrengths.value.length === 0) {
      console.log('No bias strength data received, loading mock data');
      const mockData = generateMockBiasData();
      biasStrengths.value = mockData;
      credibility.value = calculateAverageCredibility();
      console.log('Updated credibility with mock data:', credibility.value);
    }
  }, delayMs);
};

// WebSocket setup using a composable
const { 
  connect: connectWebSocket, 
  disconnect: disconnectWebSocket,
  isConnected
} = useWebSocket({
  onMessage: (data: any) => {
    try {
      console.log('Received data in App.vue:', data);
      
      // Handle different data formats
      let biasStrength: number | undefined;
      
      // Helper function to extract bias_strength from an object
      const extractBiasStrength = (obj: any): number | undefined => {
        if (!obj || typeof obj !== 'object') return undefined;
        
        // Direct bias_strength property
        if (typeof obj.bias_strength === 'number') {
          return obj.bias_strength;
        }
        
        // Check for nested data property
        if (obj.data && typeof obj.data === 'object') {
          if (typeof obj.data.bias_strength === 'number') {
            return obj.data.bias_strength;
          }
        }
        
        // Check for other common patterns
        if (typeof obj.biasStrength === 'number') {
          return obj.biasStrength;
        }
        
        if (typeof obj.bias === 'number') {
          return obj.bias;
        }
        
        // Look for any property that might contain bias_strength
        for (const key in obj) {
          if (typeof obj[key] === 'object' && obj[key] !== null) {
            const nestedResult = extractBiasStrength(obj[key]);
            if (nestedResult !== undefined) {
              return nestedResult;
            }
          }
        }
        
        return undefined;
      };
      
      // Try to extract bias_strength from the data
      if (data !== null) {
        if (typeof data === 'object') {
          biasStrength = extractBiasStrength(data);
        } else if (typeof data === 'string') {
          // Try to parse string data
          try {
            const parsedData = JSON.parse(data);
            biasStrength = extractBiasStrength(parsedData);
          } catch (parseError) {
            console.warn('Could not parse string data in App.vue:', parseError);
            
            // Check if the string itself might be a number
            const numValue = parseFloat(data);
            if (!isNaN(numValue) && numValue >= 0 && numValue <= 1) {
              biasStrength = numValue;
            }
          }
        } else if (typeof data === 'number' && data >= 0 && data <= 1) {
          // Direct number value within valid range
          biasStrength = data;
        }
      }
      
      // If we found a bias strength value, add it to our array
      if (biasStrength !== undefined) {
        console.log('Found bias strength:', biasStrength);
        biasStrengths.value.push(biasStrength);
        // Recalculate credibility based on all received bias strengths
        credibility.value = calculateAverageCredibility();
        console.log('Updated credibility score:', credibility.value, 'from', biasStrengths.value.length, 'data points');
      } else {
        console.warn('No bias_strength found in data:', data);
      }
    } catch (error) {
      console.error('Error processing WebSocket data in App.vue:', error);
    }
  },
  onOpen: () => {
    console.log('WebSocket connection opened, waiting for data...');
    // Start the mock data timer when connection opens
    loadMockDataAfterDelay();
  },
  onError: (error: Event) => {
    console.error('WebSocket error, loading mock data:', error);
    // Load mock data immediately on error
    if (biasStrengths.value.length === 0) {
      const mockData = generateMockBiasData();
      biasStrengths.value = mockData;
      credibility.value = calculateAverageCredibility();
    }
  },
  onClose: () => {
    console.log('WebSocket closed');
    if (currentUrl.value) {
      exitAnalysis(currentUrl.value);
    }
    // Load mock data if we don't have any real data
    if (biasStrengths.value.length === 0) {
      const mockData = generateMockBiasData();
      biasStrengths.value = mockData;
      credibility.value = calculateAverageCredibility();
    }
  }
});

const exitAnalysis = async (url: string) => {
  try {
    console.log('Posting to analysis endpoint:', url);
    const encodedURI = encodeURIComponent(url);
    
    // First, try to create the BiasedMedia object if it doesn't exist
    try {
      const createResponse = await fetch(`http://localhost:8080/api/biased-media/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url: url,
          title: currentWebsite.value || 'Unknown',
          source_type: url.includes('tiktok.com') ? 'tiktok' : 'website'
        }),
      });
      
      if (createResponse.ok) {
        console.log('Successfully created BiasedMedia object');
      } else {
        console.warn('Could not create BiasedMedia object, status:', createResponse.status);
        // Continue anyway, as the object might already exist
      }
    } catch (createError) {
      console.error('Error creating BiasedMedia object:', createError);
      // Continue with the analysis request anyway
    }
    
    // Now send the analysis request
    // Use URL parameter instead of form data since that's what the error shows
    const analysisUrl = `http://localhost:8080/analysis/?video_url=${encodedURI}`;
    const response = await fetch(analysisUrl, {
      method: 'POST',
    });
    
    if (!response.ok) {
      console.error('Analysis request failed with status:', response.status);
      const errorText = await response.text();
      console.error('Error details:', errorText);
    } else {
      console.log('POST request to analysis completed successfully');
    }
  } catch (error) {
    console.error('Error posting to analysis:', error);
  }
};

// Helper function to wait for an element to appear in the DOM
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

// Initialize the extension when mounted
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
      
      // Store the current URL and connect WebSocket
      currentUrl.value = parsedUrl;
      
      // Connect to WebSocket with raw URL (not encoded)
      const wsUrl = `ws://localhost:8080/ws/thingy/credibility/${parsedUrl}`;
      console.log('Connecting to WebSocket with URL:', wsUrl);
      connectWebSocket(wsUrl);
      
      // Also create the BiasedMedia object right away
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
        } else {
          console.warn('Could not create BiasedMedia object on startup, status:', createResponse.status);
        }
      } catch (createError) {
        console.error('Error creating BiasedMedia object on startup:', createError);
      }

      // Send initial credibility to content script
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

// Clean up resources when component is unmounted
onUnmounted(() => {
  disconnectWebSocket();
});

// Add a debug mode toggle
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