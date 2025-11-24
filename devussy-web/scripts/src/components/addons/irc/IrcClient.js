"use strict";
'use client';
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = IrcClient;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const button_1 = require("@/components/ui/button");
const input_1 = require("@/components/ui/input");
const scroll_area_1 = require("@/components/ui/scroll-area");
const dialog_1 = require("@/components/ui/dialog");
const lucide_react_1 = require("lucide-react");
const eventBus_1 = require("@/apps/eventBus");
const shareLinks_1 = require("@/shareLinks");
const IRC_COLORS = [
    'text-red-400',
    'text-green-400',
    'text-yellow-400',
    'text-blue-400',
    'text-purple-400',
    'text-pink-400',
    'text-cyan-400',
    'text-orange-400',
];
const getUserColor = (nick) => {
    let hash = 0;
    for (let i = 0; i < nick.length; i++) {
        hash = nick.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % IRC_COLORS.length;
    return IRC_COLORS[index];
};
const SHARE_LINK_PATTERN = '/share?payload=';
function parseShareLinkFromText(text) {
    if (!text)
        return null;
    const index = text.indexOf(SHARE_LINK_PATTERN);
    if (index === -1)
        return null;
    // Expand to capture the full URL or path (stopping at whitespace)
    let start = index;
    while (start > 0 && !/\s/.test(text[start - 1])) {
        start--;
    }
    let end = index + SHARE_LINK_PATTERN.length;
    while (end < text.length && !/\s/.test(text[end])) {
        end++;
    }
    const before = text.slice(0, start);
    const linkText = text.slice(start, end);
    const after = text.slice(end);
    let payload = '';
    try {
        let url;
        if (linkText.startsWith('http://') || linkText.startsWith('https://')) {
            url = new URL(linkText);
        }
        else {
            const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
            url = new URL(linkText, base);
        }
        payload = url.searchParams.get('payload') || '';
    }
    catch (_a) {
        const payloadIndex = linkText.indexOf('payload=');
        if (payloadIndex !== -1) {
            payload = linkText.slice(payloadIndex + 'payload='.length);
        }
    }
    if (!payload)
        return null;
    return { before, linkText, after, payload };
}
function IrcClient({ initialNick = 'Guest', defaultChannel = process.env.NEXT_PUBLIC_IRC_CHANNEL || '#devussy-chat', }) {
    var _a, _b, _c, _d;
    const [ws, setWs] = (0, react_1.useState)(null);
    const [connected, setConnected] = (0, react_1.useState)(false);
    const [demoMode, setDemoMode] = (0, react_1.useState)(false);
    const bus = (0, eventBus_1.useEventBus)();
    // Multi-conversation state
    const STATUS_TAB = 'Status';
    const [conversations, setConversations] = (0, react_1.useState)({});
    const [activeTab, setActiveTab] = (0, react_1.useState)(STATUS_TAB);
    const [nick, setNick] = (0, react_1.useState)(initialNick);
    const [inputValue, setInputValue] = (0, react_1.useState)('');
    const [newNickInput, setNewNickInput] = (0, react_1.useState)(initialNick);
    const [isNickDialogOpen, setIsNickDialogOpen] = (0, react_1.useState)(false);
    const scrollRef = (0, react_1.useRef)(null);
    const messagesEndRef = (0, react_1.useRef)(null);
    const reconnectAttempts = (0, react_1.useRef)(0);
    const maxReconnectAttempts = 3;
    const wsUrl = process.env.NEXT_PUBLIC_IRC_WS_URL ||
        (typeof window !== 'undefined'
            ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/irc/`
            : 'ws://localhost:8080/webirc/websocket/');
    // Ensure Status tab and default channel exist in state
    (0, react_1.useEffect)(() => {
        setConversations(prev => {
            const needsStatus = !prev[STATUS_TAB];
            const needsDefault = !prev[defaultChannel];
            if (!needsStatus && !needsDefault)
                return prev;
            const updates = Object.assign({}, prev);
            if (needsStatus) {
                updates[STATUS_TAB] = {
                    name: STATUS_TAB,
                    type: 'channel',
                    messages: [],
                    users: [],
                    unreadCount: 0
                };
            }
            if (needsDefault) {
                updates[defaultChannel] = {
                    name: defaultChannel,
                    type: 'channel',
                    messages: [],
                    users: [],
                    unreadCount: 0
                };
            }
            return updates;
        });
    }, [defaultChannel, STATUS_TAB]);
    // Auto-scroll logic
    (0, react_1.useEffect)(() => {
        const container = scrollRef.current;
        if (!container || !messagesEndRef.current)
            return;
        const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
        if (distanceFromBottom < 80) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [conversations, activeTab]); // Trigger on msg updates
    // Helper to add message to a specific conversation
    const addMessage = (0, react_1.useCallback)((target, msg) => {
        setConversations(prev => {
            const convName = target;
            // Create if not exists (e.g. PM)
            const existing = prev[convName] || {
                name: convName,
                type: target.startsWith('#') ? 'channel' : 'pm',
                messages: [],
                users: [],
                unreadCount: 0
            };
            return Object.assign(Object.assign({}, prev), { [convName]: Object.assign(Object.assign({}, existing), { messages: [...existing.messages, msg], unreadCount: (target !== activeTab) ? existing.unreadCount + 1 : 0 }) });
        });
    }, [activeTab]);
    // Helper to add system message to Status tab
    const addSystemMessage = (0, react_1.useCallback)((content, type = 'system') => {
        setConversations(prev => {
            const target = STATUS_TAB;
            const existing = prev[target] || {
                name: target,
                type: 'channel',
                messages: [],
                users: [],
                unreadCount: 0
            };
            return Object.assign(Object.assign({}, prev), { [target]: Object.assign(Object.assign({}, existing), { messages: [...existing.messages, {
                            id: Math.random().toString(36).substr(2, 9),
                            timestamp: new Date().toLocaleTimeString(),
                            prefix: 'system',
                            command: 'SYSTEM',
                            params: [],
                            raw: '',
                            type,
                            sender: 'System',
                            content,
                            target
                        }] }) });
        });
    }, [STATUS_TAB]);
    // Listen for cross-app events like planGenerated and surface them in chat
    (0, react_1.useEffect)(() => {
        const unsubscribe = bus.subscribe('planGenerated', (payload) => {
            const channelName = defaultChannel;
            const summaryParts = [];
            if (payload === null || payload === void 0 ? void 0 : payload.projectName) {
                summaryParts.push(`project "${payload.projectName}"`);
            }
            if (payload === null || payload === void 0 ? void 0 : payload.phaseCount) {
                summaryParts.push(`${payload.phaseCount} phases`);
            }
            const summary = summaryParts.length > 0 ? ` (${summaryParts.join(', ')})` : '';
            const content = `[Devussy] A new development plan was generated${summary}.`;
            addMessage(channelName, {
                id: Math.random().toString(36).substr(2, 9),
                timestamp: new Date().toLocaleTimeString(),
                prefix: 'devussy-bot',
                command: 'PRIVMSG',
                params: [channelName, content],
                raw: '',
                type: 'message',
                sender: 'devussy-bot',
                content,
                target: channelName,
            });
            // Also surface this as a system-level update in the Status tab
            addSystemMessage(content);
        });
        return () => {
            unsubscribe();
        };
    }, [bus, defaultChannel, addMessage, addSystemMessage]);
    // Listen for share links and execution completion events from the pipeline
    (0, react_1.useEffect)(() => {
        const unsubscribeShare = bus.subscribe('shareLinkGenerated', (payload) => {
            try {
                if (!payload || !payload.url)
                    return;
                const channelName = defaultChannel;
                const url = String(payload.url);
                const stageLabel = payload.stage || 'pipeline';
                if (!ws || !connected) {
                    addSystemMessage(`[Devussy] Share link ready for ${stageLabel}: ${url} (IRC not connected)`);
                    return;
                }
                const message = `[Devussy] Shared ${stageLabel} link: ${url}`;
                ws.send(`PRIVMSG ${channelName} :${message}\r\n`);
                // Log to Status so users always see share-link activity, even if they miss it in-channel
                addSystemMessage(message);
            }
            catch (err) {
                console.error('[IrcClient] Failed to handle shareLinkGenerated event', err);
            }
        });
        const unsubscribeExec = bus.subscribe('executionCompleted', (payload) => {
            try {
                const channelName = defaultChannel;
                const name = (payload === null || payload === void 0 ? void 0 : payload.projectName) ||
                    (payload === null || payload === void 0 ? void 0 : payload.project_name) ||
                    'a Devussy project';
                const total = payload === null || payload === void 0 ? void 0 : payload.totalPhases;
                const suffix = total ? ` (${total} phases)` : '';
                const content = `[Devussy] Execution phase completed for ${name}${suffix}.`;
                addMessage(channelName, {
                    id: Math.random().toString(36).substr(2, 9),
                    timestamp: new Date().toLocaleTimeString(),
                    prefix: 'devussy-bot',
                    command: 'PRIVMSG',
                    params: [channelName, content],
                    raw: '',
                    type: 'message',
                    sender: 'devussy-bot',
                    content,
                    target: channelName,
                });
                // Mirror execution completion into the Status tab as a system message
                addSystemMessage(content);
            }
            catch (err) {
                console.error('[IrcClient] Failed to handle executionCompleted event', err);
            }
        });
        return () => {
            unsubscribeShare();
            unsubscribeExec();
        };
    }, [bus, defaultChannel, ws, connected, addMessage, addSystemMessage]);
    // Parse IRC Message
    const parseIrcMessage = (raw) => {
        let str = raw.trim();
        let prefix = '';
        let command = '';
        let params = [];
        if (str.startsWith(':')) {
            const spaceIdx = str.indexOf(' ');
            if (spaceIdx !== -1) {
                prefix = str.slice(1, spaceIdx);
                str = str.slice(spaceIdx + 1);
            }
        }
        const spaceIdx = str.indexOf(' ');
        if (spaceIdx !== -1) {
            command = str.slice(0, spaceIdx);
            str = str.slice(spaceIdx + 1);
        }
        else {
            command = str;
            str = '';
        }
        while (str) {
            if (str.startsWith(':')) {
                params.push(str.slice(1));
                break;
            }
            const nextSpace = str.indexOf(' ');
            if (nextSpace !== -1) {
                params.push(str.slice(0, nextSpace));
                str = str.slice(nextSpace + 1);
            }
            else {
                params.push(str);
                break;
            }
        }
        let type = 'system';
        let content = '';
        let sender = prefix.split('!')[0] || prefix;
        let target = '';
        if (command === 'PRIVMSG') {
            type = 'message';
            target = params[0];
            content = params[1] || '';
        }
        else if (command === 'JOIN') {
            type = 'join';
            target = params[0].replace(/^:/, ''); // Should be channel
            content = `${sender} joined ${target}`;
        }
        else if (command === 'PART' || command === 'QUIT') {
            type = 'part';
            target = params[0]; // Often channel for PART
            content = `${sender} left: ${params[1] || 'Quit'}`;
        }
        else if (command === 'NICK') {
            type = 'nick';
            content = `${sender} is now known as ${params[0]}`;
        }
        else if (command === 'NOTICE') {
            type = 'notice';
            target = params[0];
            content = params[1] || '';
        }
        else if (command === '433') {
            type = 'error';
            content = `Nickname ${params[1]} is already in use.`;
        }
        return {
            id: Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toLocaleTimeString(),
            prefix,
            command,
            params,
            raw,
            type,
            sender,
            content,
            target
        };
    };
    // Connect to IRC
    const connect = (0, react_1.useCallback)(() => {
        if (demoMode)
            return;
        try {
            const socket = new WebSocket(wsUrl);
            socket.onopen = () => {
                setConnected(true);
                reconnectAttempts.current = 0;
                addSystemMessage('Connected to IRC Gateway');
                socket.send(`NICK ${nick}\r\n`);
                socket.send(`USER ${nick} 0 * :${nick}\r\n`);
            };
            socket.onmessage = (event) => {
                const lines = event.data.split('\r\n');
                lines.forEach((line) => {
                    if (!line)
                        return;
                    const msg = parseIrcMessage(line);
                    // Handle server PING (with or without prefix)
                    if (msg.command === 'PING') {
                        const cookie = msg.params[0] ? `:${msg.params[0]}` : '';
                        const response = `PONG ${cookie}\r\n`;
                        socket.send(response);
                        return;
                    }
                    // --- Logic for State Updates ---
                    // 1. Numeric / System
                    if (['001', '002', '003', '004', '005', '251', '252', '253', '254', '255', '366', '372', '376', '422'].includes(msg.command)) {
                        // Capture Nick from 001
                        if (msg.command === '001' && msg.params[0]) {
                            const assignedNick = msg.params[0];
                            if (assignedNick !== nick) {
                                setNick(assignedNick);
                                localStorage.setItem('devussy_irc_nick', assignedNick);
                            }
                        }
                        // Just dump into Status tab
                        if (msg.command === '376' || msg.command === '422') {
                            // End of MOTD -> Auto Join
                            socket.send(`JOIN ${defaultChannel}\r\n`);
                        }
                        // Add to Status tab to be visible
                        addMessage(STATUS_TAB, Object.assign(Object.assign({}, msg), { type: 'system', content: msg.params.slice(1).join(' ') }));
                    }
                    // 2. Names List (353)
                    else if (msg.command === '353') {
                        const channelName = msg.params[2];
                        const names = msg.params[3].split(' ').filter(n => n).map(n => {
                            let mode = '';
                            let name = n;
                            if (['@', '+', '%'].includes(n[0])) {
                                mode = n[0];
                                name = n.slice(1);
                            }
                            return { nick: name, modes: mode };
                        });
                        setConversations(prev => {
                            const c = prev[channelName];
                            if (!c)
                                return prev;
                            // Merge names
                            const existing = new Set(c.users.map(u => u.nick));
                            const newUsers = names.filter(u => !existing.has(u.nick));
                            return Object.assign(Object.assign({}, prev), { [channelName]: Object.assign(Object.assign({}, c), { users: [...c.users, ...newUsers] }) });
                        });
                    }
                    // 3. JOIN
                    else if (msg.command === 'JOIN') {
                        const channelName = msg.target || msg.params[0];
                        if (msg.sender === nick) {
                            // We joined a channel -> Create tab if missing, clear users
                            setConversations(prev => {
                                var _a;
                                return (Object.assign(Object.assign({}, prev), { [channelName]: {
                                        name: channelName,
                                        type: 'channel',
                                        messages: [...(((_a = prev[channelName]) === null || _a === void 0 ? void 0 : _a.messages) || []), msg],
                                        users: [], // Reset user list, wait for 353 or add self
                                        unreadCount: 0
                                    } }));
                            });
                            // Switch to it if we just joined? Maybe.
                            setActiveTab(channelName);
                        }
                        else {
                            // Someone else joined
                            setConversations(prev => {
                                const c = prev[channelName];
                                if (!c)
                                    return prev;
                                return Object.assign(Object.assign({}, prev), { [channelName]: Object.assign(Object.assign({}, c), { messages: [...c.messages, msg], users: [...c.users, { nick: msg.sender || 'Unknown', modes: '' }] }) });
                            });
                        }
                    }
                    // 4. PART / QUIT
                    else if (msg.command === 'PART') {
                        const channelName = msg.target || msg.params[0];
                        if (msg.sender === nick) {
                            // We left? Close tab? Or just show we left.
                            // For now just show message.
                            addMessage(channelName, msg);
                        }
                        else {
                            setConversations(prev => {
                                const c = prev[channelName];
                                if (!c)
                                    return prev;
                                return Object.assign(Object.assign({}, prev), { [channelName]: Object.assign(Object.assign({}, c), { messages: [...c.messages, msg], users: c.users.filter(u => u.nick !== msg.sender) }) });
                            });
                        }
                    }
                    else if (msg.command === 'QUIT') {
                        // Remove from ALL channels
                        setConversations(prev => {
                            const next = Object.assign({}, prev);
                            Object.keys(next).forEach(k => {
                                if (next[k].type === 'channel') {
                                    const hasUser = next[k].users.some(u => u.nick === msg.sender);
                                    if (hasUser) {
                                        next[k] = Object.assign(Object.assign({}, next[k]), { messages: [...next[k].messages, msg], users: next[k].users.filter(u => u.nick !== msg.sender) });
                                    }
                                }
                            });
                            return next;
                        });
                    }
                    // 5. PRIVMSG
                    else if (msg.command === 'PRIVMSG') {
                        if (msg.target === nick) {
                            // PM received -> Open tab for SENDER
                            const pmPartner = msg.sender || 'Unknown';
                            addMessage(pmPartner, msg);
                        }
                        else {
                            // Channel message
                            addMessage(msg.target || 'Unknown', msg);
                        }
                    }
                    // 6. NICK
                    else if (msg.command === 'NICK') {
                        const oldNick = msg.sender;
                        const newNickName = msg.params[0];
                        if (oldNick === nick) {
                            setNick(newNickName); // Update local state only when server confirms!
                            localStorage.setItem('devussy_irc_nick', newNickName);
                        }
                        // Update in all channels
                        setConversations(prev => {
                            const next = Object.assign({}, prev);
                            Object.keys(next).forEach(k => {
                                if (next[k].type === 'channel') {
                                    const userIdx = next[k].users.findIndex(u => u.nick === oldNick);
                                    if (userIdx !== -1) {
                                        const newUsers = [...next[k].users];
                                        newUsers[userIdx] = Object.assign(Object.assign({}, newUsers[userIdx]), { nick: newNickName });
                                        next[k] = Object.assign(Object.assign({}, next[k]), { users: newUsers, messages: [...next[k].messages, msg] });
                                    }
                                }
                                else if (k === oldNick) {
                                    // Rename PM tab? Complex. For now just log.
                                    next[k] = Object.assign(Object.assign({}, next[k]), { messages: [...next[k].messages, msg] });
                                }
                            });
                            return next;
                        });
                    }
                    // 7. Error
                    else if (msg.type === 'error') {
                        addSystemMessage(`Error: ${msg.content}`);
                        // Auto-retry on Nickname In Use (433)
                        if (msg.command === '433') {
                            const newNick = nick + '_';
                            // Update local state immediately so we don't loop forever on the same nick
                            setNick(newNick);
                            // Also update localStorage so next reload uses the working nick
                            localStorage.setItem('devussy_irc_nick', newNick);
                            socket.send(`NICK ${newNick}\r\n`);
                            addSystemMessage(`Nickname taken, retrying as ${newNick}...`);
                        }
                    }
                });
            };
            socket.onclose = () => {
                console.log('IRC Disconnected');
                setConnected(false);
                addSystemMessage('Disconnected from server', 'error');
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    reconnectAttempts.current++;
                    addSystemMessage(`Reconnecting in 2s... (Attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
                    setTimeout(connect, 2000);
                }
                else {
                    addSystemMessage('Could not connect. Switching to Demo Mode.');
                    setDemoMode(true);
                }
            };
            socket.onerror = (err) => {
                console.error("WebSocket error:", err);
            };
            setWs(socket);
            return () => {
                socket.close();
            };
        }
        catch (e) {
            console.error("Connection failed", e);
            setDemoMode(true);
        }
    }, [nick, defaultChannel, wsUrl, demoMode, addSystemMessage, addMessage, activeTab]); // activeTab dep is okay-ish for system msg
    // Initial load
    (0, react_1.useEffect)(() => {
        const savedNick = localStorage.getItem('devussy_irc_nick');
        if (savedNick) {
            setNick(savedNick);
            setNewNickInput(savedNick);
        }
        else {
            const randomNick = `Guest${Math.floor(1000 + Math.random() * 9000)}`;
            setNick(randomNick);
            setNewNickInput(randomNick);
            localStorage.setItem('devussy_irc_nick', randomNick);
        }
    }, []);
    const handleToggleConnection = () => {
        if (connected) {
            if (ws) {
                ws.close();
                setWs(null);
            }
            setConnected(false);
            addSystemMessage('Disconnected from server (Manual)');
        }
        else {
            connect();
        }
    };
    const handleSendMessage = (e) => {
        var _a;
        if (e)
            e.preventDefault();
        if (!inputValue.trim())
            return;
        const currentTabType = ((_a = conversations[activeTab]) === null || _a === void 0 ? void 0 : _a.type) || 'channel';
        if (inputValue.startsWith('/')) {
            const parts = inputValue.slice(1).split(' ');
            const cmd = parts[0].toUpperCase();
            if (cmd === 'NICK') {
                ws === null || ws === void 0 ? void 0 : ws.send(`NICK ${parts[1]}\r\n`);
            }
            else if (cmd === 'JOIN') {
                const channel = parts[1];
                if (channel)
                    ws === null || ws === void 0 ? void 0 : ws.send(`JOIN ${channel}\r\n`);
            }
            else if (cmd === 'PART') {
                const target = parts[1] || activeTab;
                ws === null || ws === void 0 ? void 0 : ws.send(`PART ${target}\r\n`);
                // Optionally close tab locally
                setConversations(prev => {
                    const next = Object.assign({}, prev);
                    delete next[target];
                    return next;
                });
                if (activeTab === target)
                    setActiveTab(defaultChannel);
            }
            else if (cmd === 'MSG' || cmd === 'QUERY') {
                const target = parts[1];
                const msg = parts.slice(2).join(' ');
                if (target && msg) {
                    ws === null || ws === void 0 ? void 0 : ws.send(`PRIVMSG ${target} :${msg}\r\n`);
                    // Optimistically add to PM tab
                    addMessage(target, {
                        id: Date.now().toString(),
                        timestamp: new Date().toLocaleTimeString(),
                        prefix: `${nick}!me@here`,
                        command: 'PRIVMSG',
                        params: [target, msg],
                        raw: '',
                        type: 'message',
                        sender: nick,
                        content: msg,
                        target
                    });
                    setActiveTab(target);
                }
            }
            else if (cmd === 'HELP') {
                addSystemMessage(`Available commands:
/NICK <newname> - Change nickname
/JOIN <#channel> - Join a channel
/PART [#channel] - Leave current or specific channel
/MSG <nick> <message> - Send private message
/ME <action> - Send action
/HELP - Show this help`);
            }
            else if (cmd === 'ME') {
                ws === null || ws === void 0 ? void 0 : ws.send(`PRIVMSG ${activeTab} :\u0001ACTION ${parts.slice(1).join(' ')}\u0001\r\n`);
                // Optimistic add?
            }
            else {
                addSystemMessage(`Unknown command: ${cmd}`);
            }
        }
        else {
            if (ws && connected) {
                ws.send(`PRIVMSG ${activeTab} :${inputValue}\r\n`);
                // Optimistically add OWN message to current tab
                addMessage(activeTab, {
                    id: Date.now().toString(),
                    timestamp: new Date().toLocaleTimeString(),
                    prefix: `${nick}!me@host`, // Mock prefix
                    command: 'PRIVMSG',
                    params: [activeTab, inputValue],
                    raw: '',
                    type: 'message',
                    sender: nick,
                    content: inputValue,
                    target: activeTab
                });
            }
        }
        setInputValue('');
    };
    const handleChangeNick = () => {
        if (newNickInput && newNickInput !== nick) {
            if (ws && connected) {
                ws.send(`NICK ${newNickInput}\r\n`);
                // Do NOT setNick here. Wait for server confirmation.
            }
            setIsNickDialogOpen(false);
        }
    };
    const handleUserClick = (targetNick) => {
        if (targetNick === nick)
            return;
        setConversations(prev => {
            if (prev[targetNick])
                return prev;
            return Object.assign(Object.assign({}, prev), { [targetNick]: {
                    name: targetNick,
                    type: 'pm',
                    messages: [],
                    users: [],
                    unreadCount: 0
                } });
        });
        setActiveTab(targetNick);
    };
    const closeTab = (e, tabName) => {
        var _a;
        e.stopPropagation();
        if (tabName === STATUS_TAB || tabName === defaultChannel)
            return; // Don't close Status or main
        if (((_a = conversations[tabName]) === null || _a === void 0 ? void 0 : _a.type) === 'channel') {
            ws === null || ws === void 0 ? void 0 : ws.send(`PART ${tabName}\r\n`);
        }
        setConversations(prev => {
            const next = Object.assign({}, prev);
            delete next[tabName];
            return next;
        });
        if (activeTab === tabName)
            setActiveTab(defaultChannel);
    };
    const renderMessageContent = (msg) => {
        const content = msg.content || '';
        const share = parseShareLinkFromText(content);
        if (!share) {
            return (0, jsx_runtime_1.jsx)("span", { children: content });
        }
        const handleShareClick = () => {
            try {
                const decoded = (0, shareLinks_1.decodeSharePayload)(share.payload);
                if (!decoded)
                    return;
                bus.emit('openShareLink', decoded);
            }
            catch (err) {
                console.error('[IrcClient] Failed to handle share link', err);
            }
        };
        return ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [share.before && (0, jsx_runtime_1.jsx)("span", { children: share.before }), (0, jsx_runtime_1.jsx)("button", { type: "button", onClick: handleShareClick, className: "inline-flex items-center px-1.5 py-0.5 mx-1 rounded bg-blue-600/20 text-blue-300 underline decoration-dotted hover:bg-blue-600/30 hover:text-blue-50", children: "[Open shared Devussy state]" }), share.after && (0, jsx_runtime_1.jsx)("span", { children: share.after })] }));
    };
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex h-full w-full bg-background text-foreground overflow-hidden", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex-1 flex flex-col min-w-0", children: [(0, jsx_runtime_1.jsxs)("div", { className: "border-b bg-muted/20 flex flex-col", children: [(0, jsx_runtime_1.jsxs)("div", { className: "p-2 flex justify-between items-center border-b border-white/10", children: [(0, jsx_runtime_1.jsxs)("div", { className: "font-bold flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)("span", { children: "Devussy IRC" }), demoMode && (0, jsx_runtime_1.jsx)("span", { className: "text-xs bg-yellow-600 text-white px-1 rounded", children: "DEMO" }), (0, jsx_runtime_1.jsxs)("span", { className: "text-xs text-muted-foreground ml-2", children: ["(", nick, ")"] }), (0, jsx_runtime_1.jsx)("span", { className: `text-[10px] ml-2 px-1 rounded-full border ${connected
                                                    ? 'border-green-500 text-green-400'
                                                    : demoMode
                                                        ? 'border-yellow-500 text-yellow-400'
                                                        : 'border-red-500 text-red-400'}`, children: connected ? 'Connected' : demoMode ? 'Demo mode' : 'Disconnected' })] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(button_1.Button, { variant: connected ? "destructive" : "default", size: "sm", className: "h-7 text-xs", disabled: demoMode, onClick: handleToggleConnection, children: connected ? "Disconnect" : "Connect" }), (0, jsx_runtime_1.jsxs)(dialog_1.Dialog, { open: isNickDialogOpen, onOpenChange: setIsNickDialogOpen, children: [(0, jsx_runtime_1.jsx)(dialog_1.DialogTrigger, { asChild: true, children: (0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", className: "h-7 text-xs", children: "Change Nick" }) }), (0, jsx_runtime_1.jsxs)(dialog_1.DialogContent, { children: [(0, jsx_runtime_1.jsx)(dialog_1.DialogHeader, { children: (0, jsx_runtime_1.jsx)(dialog_1.DialogTitle, { children: "Change Nickname" }) }), (0, jsx_runtime_1.jsx)("div", { className: "py-4", children: (0, jsx_runtime_1.jsx)(input_1.Input, { value: newNickInput, onChange: (e) => setNewNickInput(e.target.value), placeholder: "Enter new nickname" }) }), (0, jsx_runtime_1.jsx)(dialog_1.DialogFooter, { children: (0, jsx_runtime_1.jsx)(button_1.Button, { onClick: handleChangeNick, children: "Save" }) })] })] })] })] }), (0, jsx_runtime_1.jsx)("div", { className: "flex items-center gap-1 px-2 pt-2 overflow-x-auto", children: [STATUS_TAB, ...Object.keys(conversations).filter(k => k !== STATUS_TAB)]
                                    .filter(name => conversations[name]) // Only show tabs that exist
                                    .map(name => ((0, jsx_runtime_1.jsxs)("div", { onClick: () => {
                                        setActiveTab(name);
                                        setConversations(prev => {
                                            const conv = prev[name];
                                            if (!conv)
                                                return prev;
                                            return Object.assign(Object.assign({}, prev), { [name]: Object.assign(Object.assign({}, conv), { unreadCount: 0 }) });
                                        });
                                    }, className: `
                            group flex items-center gap-2 px-3 py-1.5 rounded-t-md cursor-pointer text-sm border-t border-l border-r select-none
                            ${activeTab === name ? 'bg-background border-border font-bold' : 'bg-muted/50 border-transparent opacity-70 hover:opacity-100'}
                        `, children: [(0, jsx_runtime_1.jsx)("span", { children: name }), conversations[name].unreadCount > 0 && ((0, jsx_runtime_1.jsx)("span", { className: "bg-red-500 text-white text-[10px] px-1 rounded-full", children: conversations[name].unreadCount })), name !== STATUS_TAB && name !== defaultChannel && ((0, jsx_runtime_1.jsx)(lucide_react_1.X, { className: "h-3 w-3 opacity-0 group-hover:opacity-100 hover:bg-red-500 hover:text-white rounded", onClick: (e) => closeTab(e, name) }))] }, name))) })] }), (0, jsx_runtime_1.jsx)("div", { ref: scrollRef, className: "flex-1 p-4 overflow-y-auto", children: (0, jsx_runtime_1.jsxs)("div", { className: "space-y-1", children: [(_a = conversations[activeTab]) === null || _a === void 0 ? void 0 : _a.messages.map((msg, i) => ((0, jsx_runtime_1.jsxs)("div", { className: "text-sm break-words font-mono", children: [(0, jsx_runtime_1.jsxs)("span", { className: "text-muted-foreground text-xs mr-2", children: ["[", msg.timestamp, "]"] }), msg.type === 'message' && ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsxs)("span", { className: `font-bold mr-2 ${getUserColor(msg.sender || '')}`, children: [msg.sender, ":"] }), renderMessageContent(msg)] })), msg.type === 'join' && ((0, jsx_runtime_1.jsxs)("span", { className: "text-green-500 italic", children: ["\u2192 ", msg.content] })), msg.type === 'part' && ((0, jsx_runtime_1.jsxs)("span", { className: "text-red-500 italic", children: ["\u2190 ", msg.content] })), msg.type === 'nick' && ((0, jsx_runtime_1.jsxs)("span", { className: "text-yellow-500 italic", children: ["\u2022 ", msg.content] })), msg.type === 'system' && ((0, jsx_runtime_1.jsxs)("span", { className: "text-muted-foreground italic", children: ["* ", msg.content] })), msg.type === 'error' && ((0, jsx_runtime_1.jsxs)("span", { className: "text-red-600 font-bold", children: ["! ", msg.content] }))] }, i))), (0, jsx_runtime_1.jsx)("div", { ref: messagesEndRef })] }) }), (0, jsx_runtime_1.jsx)("div", { className: "p-2 border-t bg-muted/10", children: (0, jsx_runtime_1.jsxs)("form", { onSubmit: handleSendMessage, className: "flex gap-2", children: [(0, jsx_runtime_1.jsx)(input_1.Input, { value: inputValue, onChange: (e) => setInputValue(e.target.value), placeholder: `Message ${activeTab}...`, className: "flex-1 font-mono" }), (0, jsx_runtime_1.jsx)(button_1.Button, { type: "submit", children: "Send" })] }) })] }), ((_b = conversations[activeTab]) === null || _b === void 0 ? void 0 : _b.type) === 'channel' && ((0, jsx_runtime_1.jsxs)("div", { className: "w-48 border-l bg-muted/10 flex flex-col hidden md:flex", children: [(0, jsx_runtime_1.jsxs)("div", { className: "p-2 border-b font-semibold text-xs uppercase tracking-wider text-muted-foreground", children: ["Users (", ((_c = conversations[activeTab]) === null || _c === void 0 ? void 0 : _c.users.length) || 0, ")"] }), (0, jsx_runtime_1.jsx)(scroll_area_1.ScrollArea, { className: "flex-1 p-2", children: (0, jsx_runtime_1.jsx)("div", { className: "space-y-1", children: (_d = conversations[activeTab]) === null || _d === void 0 ? void 0 : _d.users.sort((a, b) => a.nick.localeCompare(b.nick)).map((user) => ((0, jsx_runtime_1.jsxs)("div", { className: "text-sm flex items-center gap-1 font-mono cursor-pointer hover:bg-white/10 p-0.5 rounded", onClick: () => handleUserClick(user.nick), children: [(0, jsx_runtime_1.jsx)("span", { className: "text-muted-foreground w-3 text-center", children: user.modes }), (0, jsx_runtime_1.jsx)("span", { className: getUserColor(user.nick), children: user.nick })] }, user.nick))) }) })] }))] }));
}
