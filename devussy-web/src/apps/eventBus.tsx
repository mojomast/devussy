import React, { createContext, useContext, useRef } from "react";

class EventBus {
  private listeners: Record<string, Set<(payload: any) => void>> = {};

  emit(event: string, payload?: any) {
    const handlers = this.listeners[event];
    if (!handlers) return;
    handlers.forEach((fn) => {
      try {
        fn(payload);
      } catch (err) {
        console.error("[EventBus] handler error for", event, err);
      }
    });
  }

  subscribe(event: string, cb: (payload: any) => void): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = new Set();
    }
    this.listeners[event]!.add(cb);
    return () => {
      this.listeners[event]!.delete(cb);
      if (this.listeners[event] && this.listeners[event]!.size === 0) {
        delete this.listeners[event];
      }
    };
  }
}

const EventBusContext = createContext<EventBus | null>(null);

interface EventBusProviderProps {
  children: React.ReactNode;
}

export const EventBusProvider: React.FC<EventBusProviderProps> = ({ children }) => {
  const busRef = useRef<EventBus | null>(null);
  if (!busRef.current) {
    busRef.current = new EventBus();
  }

  return (
    <EventBusContext.Provider value={busRef.current}>
      {children}
    </EventBusContext.Provider>
  );
};

export const useEventBus = (): EventBus => {
  const bus = useContext(EventBusContext);
  if (!bus) {
    throw new Error("useEventBus must be used within an EventBusProvider");
  }
  return bus;
};

export type { EventBus };
