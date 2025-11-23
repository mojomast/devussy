import type React from "react";

export interface AppDefinition {
  id: string;
  name: string;
  icon: React.ReactNode;
  defaultSize: { width: number; height: number };
  startMenuCategory?: string;
  component: React.FC<any>;
  onOpen?: (context: AppContext) => void;
  services?: DockerServiceDef[];
  proxy?: NginxProxyDef[];
  env?: Record<string, string>;
}

export type DockerServiceDef = {
  name: string;
  image: string;
  ports?: string[];
  volumes?: string[];
  environment?: Record<string, string>;
  depends_on?: string[];
  restart?: string;
};

export type NginxProxyDef = {
  path: string;
  upstream: string;
  websocket?: boolean;
};

export interface AppContext {
  emit: (event: string, payload?: any) => void;
  subscribe: (event: string, cb: (payload: any) => void) => () => void;
  getState: () => any;
  setState: (patch: any) => void;
}
