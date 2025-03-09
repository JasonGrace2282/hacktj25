import { ref, onUnmounted } from 'vue';

interface WebSocketOptions {
  onMessage?: (data: any) => void;
  onOpen?: () => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}

export function useWebSocket(options: WebSocketOptions = {}) {
  const socket = ref<WebSocket | null>(null);
  const isConnected = ref(false);
  const lastError = ref<Event | null>(null);

  // Connect to WebSocket server
  const connect = (url: string) => {
    // Close existing connection if any
    if (socket.value) {
      console.log('Closing existing WebSocket connection');
      socket.value.close();
    }

    console.log('Attempting to connect to WebSocket:', url);
    
    // Create new WebSocket connection
    socket.value = new WebSocket(url);
    
    // Setup event handlers
    socket.value.onopen = () => {
      console.log('WebSocket connection established successfully');
      isConnected.value = true;
      if (options.onOpen) options.onOpen();
    };

    socket.value.onmessage = (event) => {
      console.log('WebSocket message received, raw data:', event.data);
      try {
        // Parse JSON data if it's a string
        let parsedData;
        try {
          if (typeof event.data === 'string') {
            // Try to parse as JSON
            try {
              parsedData = JSON.parse(event.data);
              console.log('Successfully parsed WebSocket data as JSON:', parsedData);
            } catch (jsonError) {
              console.warn('Failed to parse WebSocket data as JSON, using raw string:', event.data);
              parsedData = event.data;
            }
          } else {
            console.log('WebSocket data is not a string, using as is:', event.data);
            parsedData = event.data;
          }
        } catch (parseError) {
          console.error('Error processing WebSocket data format:', parseError);
          parsedData = event.data; // Use raw data if processing fails
        }
        
        // Log the structure of the data to help with debugging
        if (parsedData && typeof parsedData === 'object') {
          console.log('WebSocket data structure:', Object.keys(parsedData));
          if (parsedData.data && typeof parsedData.data === 'object') {
            console.log('Nested data structure:', Object.keys(parsedData.data));
          }
        }
        
        // Pass the processed data to the callback
        if (options.onMessage) options.onMessage(parsedData);
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    };

    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error);
      lastError.value = error;
      if (options.onError) options.onError(error);
    };

    socket.value.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      isConnected.value = false;
      socket.value = null;
      if (options.onClose) options.onClose();
    };
  };

  // Disconnect from WebSocket server
  const disconnect = () => {
    if (socket.value) {
      console.log('Manually closing WebSocket connection');
      socket.value.close();
      socket.value = null;
      isConnected.value = false;
    }
  };

  // Auto-cleanup on component unmount
  onUnmounted(() => {
    disconnect();
  });

  return {
    connect,
    disconnect,
    isConnected,
    lastError
  };
} 