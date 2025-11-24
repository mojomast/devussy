'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from '@/components/ui/dialog';
import { X } from 'lucide-react';
import { useEventBus } from '@/apps/eventBus';
import type { AppContext } from '@/apps/appTypes';
import { decodeSharePayload } from '@/shareLinks';

interface IrcMessage {
    id: string;
    timestamp: string;
    prefix: string;
    command: string;
    params: string[];
    raw: string;
    type: 'message' | 'notice' | 'join' | 'part' | 'nick' | 'system' | 'error';
    sender?: string;
    content?: string;
    target?: string; // Channel or Nick
}

interface IrcUser {
    nick: string;
    modes: string;
}

interface Conversation {
    name: string;
    type: 'channel' | 'pm';
    messages: IrcMessage[];
    users: IrcUser[]; // Only relevant for channels
    unreadCount: number;
}

interface IrcClientProps {
    initialNick?: string;
    defaultChannel?: string;
    appContext?: AppContext;
}

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

const getUserColor = (nick: string) => {
    let hash = 0;
    for (let i = 0; i < nick.length; i++) {
        hash = nick.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % IRC_COLORS.length;
    return IRC_COLORS[index];
};

const SHARE_LINK_PATTERN = '/share?payload=';

function parseShareLinkFromText(text: string): {
    before: string;
    linkText: string;
    after: string;
    payload: string;
} | null {
    if (!text) return null;

    const index = text.indexOf(SHARE_LINK_PATTERN);
    if (index === -1) return null;

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
        let url: URL;
        if (linkText.startsWith('http://') || linkText.startsWith('https://')) {
            url = new URL(linkText);
        } else {
            const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
            url = new URL(linkText, base);
        }
        payload = url.searchParams.get('payload') || '';
    } catch {
        const payloadIndex = linkText.indexOf('payload=');
        if (payloadIndex !== -1) {
            payload = linkText.slice(payloadIndex + 'payload='.length);
        }
    }

    if (!payload) return null;

    return { before, linkText, after, payload };
}

export default function IrcClient({
    initialNick = 'Guest',
    defaultChannel = process.env.NEXT_PUBLIC_IRC_CHANNEL || '#devussy-chat',
    appContext,
}: IrcClientProps) {
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [connected, setConnected] = useState(false);
    const [demoMode, setDemoMode] = useState(false);

    const eventBus = useEventBus();
    const bus: AppContext = useMemo(() => {
        if (appContext) {
            return appContext;
        }
        return {
            emit: (event: string, payload?: any) => {
                (eventBus as any).emit(event, payload);
            },
            subscribe: (event: string, cb: (payload: any) => void) => {
                return (eventBus as any).subscribe(event, cb);
            },
            getState: () => undefined,
            setState: (_patch: any) => { },
        };
    }, [appContext, eventBus]);

    // Multi-conversation state
    const STATUS_TAB = 'Status';
    const [conversations, setConversations] = useState<Record<string, Conversation>>({});
    const [activeTab, setActiveTab] = useState<string>(STATUS_TAB);

    const [nick, setNick] = useState(initialNick);
    const [inputValue, setInputValue] = useState('');
    const [newNickInput, setNewNickInput] = useState(initialNick);
    const [isNickDialogOpen, setIsNickDialogOpen] = useState(false);

    const scrollRef = useRef<HTMLDivElement | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 3;

    const wsUrl =
        process.env.NEXT_PUBLIC_IRC_WS_URL ||
        (typeof window !== 'undefined'
            ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/irc/`
            : 'ws://localhost:8080/webirc/websocket/');

    // Ensure Status tab and default channel exist in state
    useEffect(() => {
        setConversations(prev => {
            const needsStatus = !prev[STATUS_TAB];
            const needsDefault = !prev[defaultChannel];

            if (!needsStatus && !needsDefault) return prev;

            const updates: Record<string, Conversation> = { ...prev };

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
    useEffect(() => {
        const container = scrollRef.current;
        if (!container || !messagesEndRef.current) return;

        const distanceFromBottom =
            container.scrollHeight - container.scrollTop - container.clientHeight;

        if (distanceFromBottom < 80) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [conversations, activeTab]); // Trigger on msg updates

    // Helper to add message to a specific conversation
    const addMessage = useCallback((target: string, msg: IrcMessage) => {
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

            return {
                ...prev,
                [convName]: {
                    ...existing,
                    messages: [...existing.messages, msg],
                    unreadCount: (target !== activeTab) ? existing.unreadCount + 1 : 0
                }
            };
        });
    }, [activeTab]);

    // Helper to add system message to Status tab
    const addSystemMessage = useCallback((content: string, type: IrcMessage['type'] = 'system') => {
        setConversations(prev => {
            const target = STATUS_TAB;
            const existing = prev[target] || {
                name: target,
                type: 'channel',
                messages: [],
                users: [],
                unreadCount: 0
            };

            return {
                ...prev,
                [target]: {
                    ...existing,
                    messages: [...existing.messages, {
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
                    }]
                }
            };
        });
    }, [STATUS_TAB]);

    // Listen for cross-app events like planGenerated and surface them in chat
    useEffect(() => {
        const unsubscribe = bus.subscribe('planGenerated', (payload: any) => {
            const channelName = defaultChannel;
            const summaryParts: string[] = [];
            if (payload?.projectName) {
                summaryParts.push(`project "${payload.projectName}"`);
            }
            if (payload?.phaseCount) {
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

    // Listen for share links and execution lifecycle events from the pipeline
    useEffect(() => {
        const unsubscribeShare = bus.subscribe('shareLinkGenerated', (payload: any) => {
            try {
                if (!payload || !payload.url) return;

                const channelName = defaultChannel;
                const url = String(payload.url);
                const stageLabel = payload.stage || 'pipeline';

                if (!ws || !connected) {
                    addSystemMessage(
                        `[Devussy] Share link ready for ${stageLabel}: ${url} (IRC not connected)`,
                    );
                    return;
                }

                const message = `[Devussy] Shared ${stageLabel} link: ${url}`;
                ws.send(`PRIVMSG ${channelName} :${message}\r\n`);

                // Log to Status so users always see share-link activity, even if they miss it in-channel
                addSystemMessage(message);
            } catch (err) {
                console.error('[IrcClient] Failed to handle shareLinkGenerated event', err);
            }
        });

        const unsubscribeExec = bus.subscribe('executionCompleted', (payload: any) => {
            try {
                const channelName = defaultChannel;
                const name =
                    payload?.projectName ||
                    payload?.project_name ||
                    'a Devussy project';
                const total = payload?.totalPhases;
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
            } catch (err) {
                console.error('[IrcClient] Failed to handle executionCompleted event', err);
            }
        });

        const unsubscribeInterview = bus.subscribe('interviewCompleted', (payload: any) => {
            try {
                const channelName = defaultChannel;
                const name = payload?.projectName || 'a project';
                const content = `[Devussy] Interview completed for project "${name}".`;

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

                addSystemMessage(content);
            } catch (err) {
                console.error('[IrcClient] Failed to handle interviewCompleted event', err);
            }
        });

        const unsubscribeDesign = bus.subscribe('designCompleted', (payload: any) => {
            try {
                const channelName = defaultChannel;
                const name = payload?.projectName || 'a project';
                const content = `[Devussy] System design completed for project "${name}".`;

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

                addSystemMessage(content);
            } catch (err) {
                console.error('[IrcClient] Failed to handle designCompleted event', err);
            }
        });

        const unsubscribeExecStarted = bus.subscribe('executionStarted', (payload: any) => {
            try {
                const name =
                    payload?.projectName ||
                    payload?.project_name ||
                    'a Devussy project';
                const total = payload?.totalPhases;
                const suffix = total ? ` (${total} phases)` : '';
                const content = `[Devussy] Execution started for ${name}${suffix}.`;

                addSystemMessage(content);
            } catch (err) {
                console.error('[IrcClient] Failed to handle executionStarted event', err);
            }
        });

        const unsubscribePhase = bus.subscribe('executionPhaseUpdated', (payload: any) => {
            try {
                if (!payload || typeof payload !== 'object') return;

                const name =
                    payload.projectName ||
                    payload.project_name ||
                    'a Devussy project';

                const phaseNumber = payload.phaseNumber;
                const title = payload.phaseTitle;
                const status = payload.status;
                const total = payload.totalPhases;

                if (typeof phaseNumber !== 'number' || !status) {
                    return;
                }

                const phaseLabel = title
                    ? `phase ${phaseNumber} (${title})`
                    : `phase ${phaseNumber}`;

                const totalSuffix = total ? ` of ${total}` : '';

                let content: string | null = null;
                if (status === 'running') {
                    content = `[Devussy] Execution started for ${phaseLabel}${totalSuffix} in ${name}.`;
                } else if (status === 'complete') {
                    content = `[Devussy] Execution completed for ${phaseLabel}${totalSuffix} in ${name}.`;
                } else if (status === 'failed') {
                    content = `[Devussy] Execution failed for ${phaseLabel}${totalSuffix} in ${name}.`;
                }

                if (content) {
                    addSystemMessage(content);
                }
            } catch (err) {
                console.error('[IrcClient] Failed to handle executionPhaseUpdated event', err);
            }
        });

        return () => {
            unsubscribeShare();
            unsubscribeExec();
            unsubscribeInterview();
            unsubscribeDesign();
            unsubscribeExecStarted();
            unsubscribePhase();
        };
    }, [bus, defaultChannel, ws, connected, addMessage, addSystemMessage]);

    // Parse IRC Message
    const parseIrcMessage = (raw: string): IrcMessage => {
        let str = raw.trim();
        let prefix = '';
        let command = '';
        let params: string[] = [];

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
        } else {
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
            } else {
                params.push(str);
                break;
            }
        }

        let type: IrcMessage['type'] = 'system';
        let content = '';
        let sender = prefix.split('!')[0] || prefix;
        let target = '';

        if (command === 'PRIVMSG') {
            type = 'message';
            target = params[0];
            content = params[1] || '';
        } else if (command === 'JOIN') {
            type = 'join';
            target = params[0].replace(/^:/, ''); // Should be channel
            content = `${sender} joined ${target}`;
        } else if (command === 'PART' || command === 'QUIT') {
            type = 'part';
            target = params[0]; // Often channel for PART
            content = `${sender} left: ${params[1] || 'Quit'}`;
        } else if (command === 'NICK') {
            type = 'nick';
            content = `${sender} is now known as ${params[0]}`;
        } else if (command === 'NOTICE') {
            type = 'notice';
            target = params[0];
            content = params[1] || '';
        } else if (command === '433') {
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
    const connect = useCallback(() => {
        if (demoMode) return;

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
                lines.forEach((line: string) => {
                    if (!line) return;

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
                        addMessage(STATUS_TAB, { ...msg, type: 'system', content: msg.params.slice(1).join(' ') });
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
                            if (!c) return prev;
                            // Merge names
                            const existing = new Set(c.users.map(u => u.nick));
                            const newUsers = names.filter(u => !existing.has(u.nick));
                            return { ...prev, [channelName]: { ...c, users: [...c.users, ...newUsers] } };
                        });
                    }
                    // 3. JOIN
                    else if (msg.command === 'JOIN') {
                        const channelName = msg.target || msg.params[0];
                        if (msg.sender === nick) {
                            // We joined a channel -> Create tab if missing, clear users
                            setConversations(prev => ({
                                ...prev,
                                [channelName]: {
                                    name: channelName,
                                    type: 'channel',
                                    messages: [...(prev[channelName]?.messages || []), msg],
                                    users: [], // Reset user list, wait for 353 or add self
                                    unreadCount: 0
                                }
                            }));
                            // Switch to it if we just joined? Maybe.
                            setActiveTab(channelName);
                        } else {
                            // Someone else joined
                            setConversations(prev => {
                                const c = prev[channelName];
                                if (!c) return prev;
                                return {
                                    ...prev,
                                    [channelName]: {
                                        ...c,
                                        messages: [...c.messages, msg],
                                        users: [...c.users, { nick: msg.sender || 'Unknown', modes: '' }]
                                    }
                                };
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
                        } else {
                            setConversations(prev => {
                                const c = prev[channelName];
                                if (!c) return prev;
                                return {
                                    ...prev,
                                    [channelName]: {
                                        ...c,
                                        messages: [...c.messages, msg],
                                        users: c.users.filter(u => u.nick !== msg.sender)
                                    }
                                };
                            });
                        }
                    }
                    else if (msg.command === 'QUIT') {
                        // Remove from ALL channels
                        setConversations(prev => {
                            const next = { ...prev };
                            Object.keys(next).forEach(k => {
                                if (next[k].type === 'channel') {
                                    const hasUser = next[k].users.some(u => u.nick === msg.sender);
                                    if (hasUser) {
                                        next[k] = {
                                            ...next[k],
                                            messages: [...next[k].messages, msg],
                                            users: next[k].users.filter(u => u.nick !== msg.sender)
                                        };
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
                        } else {
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
                            const next = { ...prev };
                            Object.keys(next).forEach(k => {
                                if (next[k].type === 'channel') {
                                    const userIdx = next[k].users.findIndex(u => u.nick === oldNick);
                                    if (userIdx !== -1) {
                                        const newUsers = [...next[k].users];
                                        newUsers[userIdx] = { ...newUsers[userIdx], nick: newNickName };
                                        next[k] = {
                                            ...next[k],
                                            users: newUsers,
                                            messages: [...next[k].messages, msg]
                                        };
                                    }
                                } else if (k === oldNick) {
                                    // Rename PM tab? Complex. For now just log.
                                    next[k] = {
                                        ...next[k],
                                        messages: [...next[k].messages, msg]
                                    };
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
                } else {
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
        } catch (e) {
            console.error("Connection failed", e);
            setDemoMode(true);
        }
    }, [nick, defaultChannel, wsUrl, demoMode, addSystemMessage, addMessage, activeTab]); // activeTab dep is okay-ish for system msg

    // Initial load
    useEffect(() => {
        const savedNick = localStorage.getItem('devussy_irc_nick');
        if (savedNick) {
            setNick(savedNick);
            setNewNickInput(savedNick);
        } else {
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
        } else {
            connect();
        }
    };

    const handleSendMessage = (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!inputValue.trim()) return;

        const currentTabType = conversations[activeTab]?.type || 'channel';

        if (inputValue.startsWith('/')) {
            const parts = inputValue.slice(1).split(' ');
            const cmd = parts[0].toUpperCase();

            if (cmd === 'NICK') {
                ws?.send(`NICK ${parts[1]}\r\n`);
            } else if (cmd === 'JOIN') {
                const channel = parts[1];
                if (channel) ws?.send(`JOIN ${channel}\r\n`);
            } else if (cmd === 'PART') {
                const target = parts[1] || activeTab;
                ws?.send(`PART ${target}\r\n`);
                // Optionally close tab locally
                setConversations(prev => {
                    const next = { ...prev };
                    delete next[target];
                    return next;
                });
                if (activeTab === target) setActiveTab(defaultChannel);
            } else if (cmd === 'MSG' || cmd === 'QUERY') {
                const target = parts[1];
                const msg = parts.slice(2).join(' ');
                if (target && msg) {
                    ws?.send(`PRIVMSG ${target} :${msg}\r\n`);
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
            } else if (cmd === 'HELP') {
                addSystemMessage(`Available commands:
/NICK <newname> - Change nickname
/JOIN <#channel> - Join a channel
/PART [#channel] - Leave current or specific channel
/MSG <nick> <message> - Send private message
/ME <action> - Send action
/HELP - Show this help`);
            } else if (cmd === 'ME') {
                ws?.send(`PRIVMSG ${activeTab} :\u0001ACTION ${parts.slice(1).join(' ')}\u0001\r\n`);
                // Optimistic add?
            } else {
                addSystemMessage(`Unknown command: ${cmd}`);
            }
        } else {
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

    const handleUserClick = (targetNick: string) => {
        if (targetNick === nick) return;
        setConversations(prev => {
            if (prev[targetNick]) return prev;
            return {
                ...prev,
                [targetNick]: {
                    name: targetNick,
                    type: 'pm',
                    messages: [],
                    users: [],
                    unreadCount: 0
                }
            };
        });
        setActiveTab(targetNick);
    };

    const closeTab = (e: React.MouseEvent, tabName: string) => {
        e.stopPropagation();
        if (tabName === STATUS_TAB || tabName === defaultChannel) return; // Don't close Status or main

        if (conversations[tabName]?.type === 'channel') {
            ws?.send(`PART ${tabName}\r\n`);
        }

        setConversations(prev => {
            const next = { ...prev };
            delete next[tabName];
            return next;
        });
        if (activeTab === tabName) setActiveTab(defaultChannel);
    };

    const renderMessageContent = (msg: IrcMessage) => {
        const content = msg.content || '';
        const share = parseShareLinkFromText(content);

        if (!share) {
            return <span>{content}</span>;
        }

        const handleShareClick = () => {
            try {
                const decoded = decodeSharePayload(share.payload);
                if (!decoded) return;
                bus.emit('openShareLink', decoded);
            } catch (err) {
                console.error('[IrcClient] Failed to handle share link', err);
            }
        };

        return (
            <>
                {share.before && <span>{share.before}</span>}
                <button
                    type="button"
                    onClick={handleShareClick}
                    className="inline-flex items-center px-1.5 py-0.5 mx-1 rounded bg-blue-600/20 text-blue-300 underline decoration-dotted hover:bg-blue-600/30 hover:text-blue-50"
                >
                    [Open shared Devussy state]
                </button>
                {share.after && <span>{share.after}</span>}
            </>
        );
    };

    return (
        <div className="flex h-full w-full bg-background text-foreground overflow-hidden">
            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col min-w-0">
                <div className="border-b bg-muted/20 flex flex-col">
                    <div className="p-2 flex justify-between items-center border-b border-white/10">
                        <div className="font-bold flex items-center gap-2">
                            <span>Devussy IRC</span>
                            {demoMode && <span className="text-xs bg-yellow-600 text-white px-1 rounded">DEMO</span>}
                            <span className="text-xs text-muted-foreground ml-2">({nick})</span>
                            <span
                                className={`text-[10px] ml-2 px-1 rounded-full border ${connected
                                    ? 'border-green-500 text-green-400'
                                    : demoMode
                                        ? 'border-yellow-500 text-yellow-400'
                                        : 'border-red-500 text-red-400'
                                    }`}
                            >
                                {connected ? 'Connected' : demoMode ? 'Demo mode' : 'Disconnected'}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                variant={connected ? "destructive" : "default"}
                                size="sm"
                                className="h-7 text-xs"
                                disabled={demoMode}
                                onClick={handleToggleConnection}
                            >
                                {connected ? "Disconnect" : "Connect"}
                            </Button>
                            <Dialog open={isNickDialogOpen} onOpenChange={setIsNickDialogOpen}>
                                <DialogTrigger asChild>
                                    <Button variant="outline" size="sm" className="h-7 text-xs">Change Nick</Button>
                                </DialogTrigger>
                                <DialogContent>
                                    <DialogHeader>
                                        <DialogTitle>Change Nickname</DialogTitle>
                                    </DialogHeader>
                                    <div className="py-4">
                                        <Input
                                            value={newNickInput}
                                            onChange={(e) => setNewNickInput(e.target.value)}
                                            placeholder="Enter new nickname"
                                        />
                                    </div>
                                    <DialogFooter>
                                        <Button onClick={handleChangeNick}>Save</Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex items-center gap-1 px-2 pt-2 overflow-x-auto">
                        {[STATUS_TAB, ...Object.keys(conversations).filter(k => k !== STATUS_TAB)]
                            .filter(name => conversations[name]) // Only show tabs that exist
                            .map(name => (
                                <div
                                    key={name}
                                    onClick={() => {
                                        setActiveTab(name);
                                        setConversations(prev => {
                                            const conv = prev[name];
                                            if (!conv) return prev;
                                            return {
                                                ...prev,
                                                [name]: {
                                                    ...conv,
                                                    unreadCount: 0,
                                                },
                                            };
                                        });
                                    }}
                                    className={`
                            group flex items-center gap-2 px-3 py-1.5 rounded-t-md cursor-pointer text-sm border-t border-l border-r select-none
                            ${activeTab === name ? 'bg-background border-border font-bold' : 'bg-muted/50 border-transparent opacity-70 hover:opacity-100'}
                        `}
                                >
                                    <span>{name}</span>
                                    {conversations[name].unreadCount > 0 && (
                                        <span className="bg-red-500 text-white text-[10px] px-1 rounded-full">{conversations[name].unreadCount}</span>
                                    )}
                                    {name !== STATUS_TAB && name !== defaultChannel && (
                                        <X
                                            className="h-3 w-3 opacity-0 group-hover:opacity-100 hover:bg-red-500 hover:text-white rounded"
                                            onClick={(e) => closeTab(e, name)}
                                        />
                                    )}
                                </div>
                            ))}
                    </div>
                </div>

                <div ref={scrollRef} className="flex-1 p-4 overflow-y-auto">
                    <div className="space-y-1">
                        {conversations[activeTab]?.messages.map((msg, i) => (
                            <div key={i} className="text-sm break-words font-mono">
                                <span className="text-muted-foreground text-xs mr-2">[{msg.timestamp}]</span>
                                {msg.type === 'message' && (
                                    <>
                                        <span className={`font-bold mr-2 ${getUserColor(msg.sender || '')}`}>{msg.sender}:</span>
                                        {renderMessageContent(msg)}
                                    </>
                                )}
                                {msg.type === 'join' && (
                                    <span className="text-green-500 italic">→ {msg.content}</span>
                                )}
                                {msg.type === 'part' && (
                                    <span className="text-red-500 italic">← {msg.content}</span>
                                )}
                                {msg.type === 'nick' && (
                                    <span className="text-yellow-500 italic">• {msg.content}</span>
                                )}
                                {msg.type === 'system' && (
                                    <span className="text-muted-foreground italic">* {msg.content}</span>
                                )}
                                {msg.type === 'error' && (
                                    <span className="text-red-600 font-bold">! {msg.content}</span>
                                )}
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                <div className="p-2 border-t bg-muted/10">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                        <Input
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder={`Message ${activeTab}...`}
                            className="flex-1 font-mono"
                        />
                        <Button type="submit">Send</Button>
                    </form>
                </div>
            </div>

            {/* User List Sidebar (Only for channels) */}
            {conversations[activeTab]?.type === 'channel' && (
                <div className="w-48 border-l bg-muted/10 flex flex-col hidden md:flex">
                    <div className="p-2 border-b font-semibold text-xs uppercase tracking-wider text-muted-foreground">
                        Users ({conversations[activeTab]?.users.length || 0})
                    </div>
                    <ScrollArea className="flex-1 p-2">
                        <div className="space-y-1">
                            {conversations[activeTab]?.users.sort((a, b) => a.nick.localeCompare(b.nick)).map((user) => (
                                <div
                                    key={user.nick}
                                    className="text-sm flex items-center gap-1 font-mono cursor-pointer hover:bg-white/10 p-0.5 rounded"
                                    onClick={() => handleUserClick(user.nick)}
                                >
                                    <span className="text-muted-foreground w-3 text-center">{user.modes}</span>
                                    <span className={getUserColor(user.nick)}>{user.nick}</span>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                </div>
            )}
        </div>
    );
}
