import React, { createContext, useContext, useRef } from "react";
import type { ShareLinkPayload } from "@/shareLinks";

type EventPayloads = {
  planGenerated: {
    projectName?: string;
    languages?: string;
    requirements?: string;
    plan: any;
    phaseCount?: number;
  };
  executionStarted: {
    projectName?: string;
    totalPhases?: number;
  };
  interviewCompleted: {
    projectName?: string;
    requirements?: string;
    languages?: string;
  };
  designCompleted: {
    projectName?: string;
    design: any;
  };
  shareLinkGenerated: {
    stage: string;
    data: any;
    url: string;
  };
  executionCompleted: {
    projectName?: string;
    plan?: any;
    totalPhases?: number;
  };
  openShareLink: ShareLinkPayload;
  // Fallback for any future or ad-hoc events
  [event: string]: any;
};

type EventKey = keyof EventPayloads;

class EventBus {
  private listeners: { [K in EventKey]?: Set<(payload: EventPayloads[K]) => void> } = {};

  emit<K extends EventKey>(event: K, payload: EventPayloads[K]) {
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

  subscribe<K extends EventKey>(event: K, cb: (payload: EventPayloads[K]) => void): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = new Set();
    }
    this.listeners[event]!.add(cb as (payload: EventPayloads[K]) => void);
    return () => {
      this.listeners[event]!.delete(cb as (payload: EventPayloads[K]) => void);
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
