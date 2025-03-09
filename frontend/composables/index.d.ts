declare module '../composables/useWebSocket' {
  interface WebSocketOptions {
    onMessage?: (data: any) => void;
    onOpen?: () => void;
    onError?: (error: Event) => void;
    onClose?: () => void;
  }

  export function useWebSocket(options?: WebSocketOptions): {
    connect: (url: string) => void;
    disconnect: () => void;
    isConnected: import('vue').Ref<boolean>;
    lastError: import('vue').Ref<Event | null>;
  };
} 