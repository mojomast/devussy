'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
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
}

interface IrcUser {
  nick: string;
  modes: string;
}

interface IrcClientProps {
  initialNick?: string;
  channel?: string;
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

export default function IrcClient({
  initialNick = 'Guest',
  channel = process.env.NEXT_PUBLIC_IRC_CHANNEL || '#devussy-chat',
}: IrcClientProps) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [messages, setMessages] = useState<IrcMessage[]>([]);
  const [users, setUsers] = useState<IrcUser[]>([]);
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
      ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/irc/webirc/websocket/`
      : 'ws://localhost:8080/webirc/websocket/');

  // Auto-scroll to bottom when user is already near the bottom
  useEffect(() => {
    const container = scrollRef.current;
    if (!container || !messagesEndRef.current) return;

    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    if (distanceFromBottom < 80) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Helper to add system message
  const addSystemMessage = useCallback((content: string, type: IrcMessage['type'] = 'system') => {
    setMessages((prev) => [
      ...prev,
      {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toLocaleTimeString(),
        prefix: 'system',
        command: 'SYSTEM',
        params: [],
        raw: '',
        type,
        sender: 'System',
        content,
      },
    ]);
  }, []);

  // Parse IRC Message
  const parseIrcMessage = (raw: string): IrcMessage => {
    // Simple IRC parser
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

    // Determine high-level type and content
    let type: IrcMessage['type'] = 'system';
    let content = '';
    let sender = prefix.split('!')[0] || prefix;

    if (command === 'PRIVMSG') {
      type = 'message';
      content = params[1] || '';
    } else if (command === 'JOIN') {
      type = 'join';
      content = `${sender} joined the channel`;
    } else if (command === 'PART' || command === 'QUIT') {
      type = 'part';
      content = `${sender} left the channel`;
    } else if (command === 'NICK') {
      type = 'nick';
      content = `${sender} is now known as ${params[0]}`;
    } else if (command === 'NOTICE') {
      type = 'notice';
      content = params[1] || '';
    } else if (command === '433') { // ERR_NICKNAMEINUSE
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
    };
  };

  // Connect to IRC
  const connect = useCallback(() => {
    if (demoMode) return;
    
    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('IRC Connected');
        setConnected(true);
        reconnectAttempts.current = 0;
        addSystemMessage('Connected to IRC Gateway');
        
        // Register
        socket.send(`NICK ${nick}\r\n`);
        socket.send(`USER ${nick} 0 * :${nick}\r\n`);
      };

      socket.onmessage = (event) => {
        const lines = event.data.split('\r\n');
        lines.forEach((line: string) => {
          if (!line) return;
          console.log('IN:', line);
          
          // Handle PING/PONG immediately
          if (line.startsWith('PING')) {
            const response = `PONG ${line.slice(5)}\r\n`;
            socket.send(response);
            return;
          }

          const msg = parseIrcMessage(line);

          // Filter out some numeric replies to reduce noise, but keep important ones
          if (['001', '002', '003', '004', '005', '251', '252', '253', '254', '255', '366'].includes(msg.command)) {
             // Log silently or minimal
          } else if (msg.command === '376' || msg.command === '422') { // End of MOTD or No MOTD
             // Auto-join channel after welcome
             socket.send(`JOIN ${channel}\r\n`);
             addSystemMessage(`Joined ${channel}`);
          } else if (msg.command === '353') { // RPL_NAMREPLY
             // Update user list
             // params: [target, type, channel, names]
             if (msg.params[3]) {
                 const names = msg.params[3].split(' ').filter(n => n).map(n => {
                     let mode = '';
                     let name = n;
                     if (['@', '+', '%'].includes(n[0])) {
                         mode = n[0];
                         name = n.slice(1);
                     }
                     return { nick: name, modes: mode };
                 });
                 setUsers(prev => {
                     // Simple merge or replace? RPL_NAMREPLY can be multiple lines.
                     // For simplicity, we'll just append and dedup later or reset on join.
                     // A proper implementation tracks 353 sequence and 366 end of names.
                     // Here we just add them.
                     const existing = new Set(prev.map(u => u.nick));
                     const newUsers = names.filter(u => !existing.has(u.nick));
                     return [...prev, ...newUsers];
                 });
             }
          } else if (msg.command === 'JOIN') {
              if (msg.sender === nick) {
                  // We joined, clear users to rebuild list
                  setUsers([]); 
              } else {
                  setUsers(prev => [...prev, { nick: msg.sender || 'Unknown', modes: '' }]);
              }
              setMessages(prev => [...prev, msg]);
          } else if (msg.command === 'PART' || msg.command === 'QUIT') {
              setUsers(prev => prev.filter(u => u.nick !== msg.sender));
              setMessages(prev => [...prev, msg]);
          } else if (msg.command === 'NICK') {
               const oldNick = msg.sender;
               const newNick = msg.params[0];
               if (oldNick === nick) {
                   setNick(newNick);
               }
               setUsers(prev => prev.map(u => u.nick === oldNick ? { ...u, nick: newNick } : u));
               setMessages(prev => [...prev, msg]);
          } else {
              // Default handling
              if (msg.content || msg.type === 'error') {
                   setMessages(prev => [...prev, msg]);
              }
          }
        });
      };

      socket.onclose = () => {
        console.log('IRC Disconnected');
        setConnected(false);
        setUsers([]);
        addSystemMessage('Disconnected from server', 'error');
        
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          addSystemMessage(`Reconnecting in 2s... (Attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
          setTimeout(connect, 2000);
        } else {
          addSystemMessage('Could not connect to IRC server. Switching to Demo Mode.');
          setDemoMode(true);
        }
      };
      
      socket.onerror = (err) => {
          console.error("WebSocket error:", err);
          // onclose will trigger
      };

      setWs(socket);

      return () => {
        socket.close();
      };
    } catch (e) {
        console.error("Connection failed", e);
        setDemoMode(true);
    }
  }, [nick, channel, wsUrl, demoMode, addSystemMessage]);

  useEffect(() => {
    // Load persisted nick
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

    // Load persisted messages
    try {
        const savedMessages = localStorage.getItem('devussy_irc_messages');
        if (savedMessages) {
            setMessages(JSON.parse(savedMessages));
        }
    } catch (e) {}

    if (!demoMode) {
        const cleanup = connect();
        return () => {
            if (cleanup) cleanup();
        };
    }
  }, [connect, demoMode]);

  // Persist messages
  useEffect(() => {
      if (messages.length > 0) {
          const recent = messages.slice(-50);
          localStorage.setItem('devussy_irc_messages', JSON.stringify(recent));
      }
  }, [messages]);

  // Demo Mode Simulation
  useEffect(() => {
    if (demoMode) {
      addSystemMessage('*** DEMO MODE ACTIVATED ***');
      setConnected(true);
      setUsers([
          { nick: 'System', modes: '@' },
          { nick: 'User1', modes: '' },
          { nick: 'User2', modes: '' },
          { nick, modes: '' }
      ]);
      
      const interval = setInterval(() => {
          const randomUser = `User${Math.floor(Math.random() * 5) + 1}`;
          const randomMsgs = [
              "Hello world!",
              "Is the pipeline running?",
              "Check the logs.",
              "Nice update!",
              "brb coffee"
          ];
          const text = randomMsgs[Math.floor(Math.random() * randomMsgs.length)];
          
          setMessages(prev => [...prev, {
              id: Math.random().toString(36).substr(2, 9),
              timestamp: new Date().toLocaleTimeString(),
              prefix: `${randomUser}!user@host`,
              command: 'PRIVMSG',
              params: [channel, text],
              raw: '',
              type: 'message',
              sender: randomUser,
              content: text
          }]);
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [demoMode, channel, nick, addSystemMessage]);


  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) return;

    if (demoMode) {
        setMessages(prev => [...prev, {
            id: Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toLocaleTimeString(),
            prefix: `${nick}!user@host`,
            command: 'PRIVMSG',
            params: [channel, inputValue],
            raw: '',
            type: 'message',
            sender: nick,
            content: inputValue
        }]);
    } else if (ws && connected) {
        if (inputValue.startsWith('/')) {
            // Handle slash commands
            const parts = inputValue.slice(1).split(' ');
            const cmd = parts[0].toUpperCase();
            if (cmd === 'NICK') {
                const newName = parts[1];
                if (newName) {
                    ws.send(`NICK ${newName}\r\n`);
                }
            } else if (cmd === 'JOIN') {
                ws.send(`JOIN ${parts[1]}\r\n`);
            } else if (cmd === 'PART') {
                ws.send(`PART ${parts[1] || channel}\r\n`);
            } else if (cmd === 'ME') {
                ws.send(`PRIVMSG ${channel} :\u0001ACTION ${parts.slice(1).join(' ')}\u0001\r\n`);
            } else {
                addSystemMessage(`Unknown command: ${cmd}`);
            }
        } else {
            ws.send(`PRIVMSG ${channel} :${inputValue}\r\n`);
            // Own messages are not echoed by IRC servers usually, so we add it manually
            setMessages(prev => [...prev, {
                id: Math.random().toString(36).substr(2, 9),
                timestamp: new Date().toLocaleTimeString(),
                prefix: `${nick}!user@host`,
                command: 'PRIVMSG',
                params: [channel, inputValue],
                raw: '',
                type: 'message',
                sender: nick,
                content: inputValue
            }]);
        }
    }
    setInputValue('');
  };

  const handleChangeNick = () => {
      if (newNickInput && newNickInput !== nick) {
          if (demoMode) {
              setNick(newNickInput);
              addSystemMessage(`You are now known as ${newNickInput}`);
          } else if (ws && connected) {
              ws.send(`NICK ${newNickInput}\r\n`);
          }
          localStorage.setItem('devussy_irc_nick', newNickInput);
          setIsNickDialogOpen(false);
      }
  };

  return (
    <div className="flex h-full w-full bg-background text-foreground overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
         <div className="p-2 border-b flex justify-between items-center bg-muted/20">
             <div className="font-bold">{channel} {demoMode && <span className="text-xs bg-yellow-600 text-white px-1 rounded ml-2">DEMO</span>}</div>
             <Dialog open={isNickDialogOpen} onOpenChange={setIsNickDialogOpen}>
                 <DialogTrigger asChild>
                     <Button variant="outline" size="sm">Change Nick</Button>
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
         
         <div ref={scrollRef} className="flex-1 p-4 overflow-y-auto">
             <div className="space-y-1">
                 {messages.map((msg) => (
                     <div key={msg.id} className="text-sm break-words font-mono">
                         <span className="text-muted-foreground text-xs mr-2">[{msg.timestamp}]</span>
                         {msg.type === 'message' && (
                             <>
                                 <span className={`font-bold mr-2 ${getUserColor(msg.sender || '')}`}>{msg.sender}:</span>
                                 <span>{msg.content}</span>
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
                    placeholder={`Message ${channel}...`}
                    className="flex-1 font-mono"
                 />
                 <Button type="submit">Send</Button>
             </form>
         </div>
      </div>

      {/* User List Sidebar */}
      <div className="w-48 border-l bg-muted/10 flex flex-col hidden md:flex">
          <div className="p-2 border-b font-semibold text-xs uppercase tracking-wider text-muted-foreground">
              Users ({users.length})
          </div>
          <ScrollArea className="flex-1 p-2">
              <div className="space-y-1">
                  {users.sort((a,b) => a.nick.localeCompare(b.nick)).map((user) => (
                      <div key={user.nick} className="text-sm flex items-center gap-1 font-mono">
                          <span className="text-muted-foreground w-3 text-center">{user.modes}</span>
                          <span className={getUserColor(user.nick)}>{user.nick}</span>
                      </div>
                  ))}
              </div>
          </ScrollArea>
      </div>
    </div>
  );
}
