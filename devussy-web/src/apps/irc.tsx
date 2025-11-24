import React from "react";
import type { AppDefinition } from "./appTypes";
import { MessageSquare } from "lucide-react";
import IrcClient from "@/components/addons/irc/IrcClient";

const IrcApp: AppDefinition = {
  id: "irc",
  name: "IRC Chat",
  icon: <MessageSquare className="w-4 h-4" />,
  defaultSize: { width: 800, height: 600 },
  startMenuCategory: "Communication",
  singleInstance: true,
  component: IrcClient,
  services: [
    {
      name: "ircd",
      image: "inspircd/inspircd-docker:latest",
      ports: ["6667:6667", "8080:8080"],
      volumes: [
        "./irc/conf/inspircd_v2.conf:/inspircd/conf/inspircd.conf",
        "./irc/logs:/inspircd/logs",
        "./irc/data:/inspircd/data",
      ],
      restart: "unless-stopped",
    },
  ],
  proxy: [
    {
      path: "/apps/irc/ws/",
      upstream: "ircd:8080",
      websocket: true,
    },
  ],
  env: {
    NEXT_PUBLIC_IRC_WS_URL: "wss://dev.ussy.host/ws/irc/",
    NEXT_PUBLIC_IRC_CHANNEL: "#devussy-chat",
  },
};

export default IrcApp;
