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
  component: IrcClient,
};

export default IrcApp;
