"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const lucide_react_1 = require("lucide-react");
const IrcClient_1 = __importDefault(require("@/components/addons/irc/IrcClient"));
const IrcApp = {
    id: "irc",
    name: "IRC Chat",
    icon: (0, jsx_runtime_1.jsx)(lucide_react_1.MessageSquare, { className: "w-4 h-4" }),
    defaultSize: { width: 800, height: 600 },
    startMenuCategory: "Communication",
    component: IrcClient_1.default,
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
exports.default = IrcApp;
