"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Users, Settings, MessageSquare } from "lucide-react";
import { useTheme } from "@/components/theme/ThemeProvider";

interface IrcMessage {
  type: 'join' | 'part' | 'message' | 'system' | 'nick';
  user?: string;
  message: string;
  timestamp: Date;
}

interface IrcUser {
  nick: string;
  mode?: string;
}

export const IrcView: React.FC = () => {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<IrcMessage[]>([]);
  const [users, setUsers] = useState<IrcUser[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [nickname, setNickname] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [showNickChange, setShowNickChange] = useState(false);
  const [tempNick, setTempNick] = useState('');
  const [isDemoMode, setIsDemoMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize nickname from localStorage or generate random
  useEffect(() => {
    const savedNick = localStorage.getItem('irc-nickname');
    if (savedNick) {
      setNickname(savedNick);
    } else {
      const randomNick = `User${Math.floor(Math.random() * 10000)}`;
      setNickname(randomNick);
      localStorage.setItem('irc-nickname', randomNick);
    }
  }, []);

  // Demo mode - simulate IRC activity
  useEffect(() => {
    if (!nickname) return;

    const connectWebSocket = () => {
      try {
        const wsUrl = theme === 'bliss' 
          ? 'wss://irc-ws.ussy.host/ws'
          : 'wss://irc-ws.ussy.host/ws';
        
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          setIsConnected(true);
          setIsDemoMode(false);
          setMessages(prev => [...prev, {
            type: 'system',
            message: 'Connected to IRC server',
            timestamp: new Date()
          }]);
          
          // Send initial commands
          wsRef.current?.send(JSON.stringify({
            cmd: 'NICK',
            nick: nickname
          }));
          
          wsRef.current?.send(JSON.stringify({
            cmd: 'JOIN',
            channel: '#devussy'
          }));
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            switch (data.cmd) {
              case 'PRIVMSG':
                setMessages(prev => [...prev, {
                  type: 'message',
                  user: data.nick,
                  message: data.message,
                  timestamp: new Date()
                }]);
                break;
                
              case 'JOIN':
                if (data.nick !== nickname) {
                  setMessages(prev => [...prev, {
                    type: 'join',
                    user: data.nick,
                    message: 'joined the channel',
                    timestamp: new Date()
                  }]);
                }
                break;
                
              case 'PART':
                setMessages(prev => [...prev, {
                  type: 'part',
                  user: data.nick,
                  message: 'left the channel',
                  timestamp: new Date()
                }]);
                break;
                
              case 'NICK':
                setUsers(prev => data.users || []);
                break;
                
              case '353': // RPL_NAMREPLY - user list
                setUsers(prev => data.nicks.map((nick: string) => ({ nick })));
                break;
                
              case 'system':
                setMessages(prev => [...prev, {
                  type: 'system',
                  message: data.message,
                  timestamp: new Date()
                }]);
                break;
            }
          } catch (e) {
            console.error('Failed to parse IRC message:', e);
          }
        };

        wsRef.current.onclose = () => {
          setIsConnected(false);
          setMessages(prev => [...prev, {
            type: 'system',
            message: 'Disconnected from IRC server',
            timestamp: new Date()
          }]);
          
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setMessages(prev => [...prev, {
            type: 'system',
            message: 'Connection error',
            timestamp: new Date()
          }]);
        };
      } catch (error) {
        console.error('Failed to connect to IRC:', error);
        setMessages(prev => [...prev, {
          type: 'system',
          message: 'Failed to connect to IRC server',
          timestamp: new Date()
        }]);
      }
    };

    // Try real connection first, fallback to demo mode after timeout
    connectWebSocket();
    
    const timeoutId = setTimeout(() => {
      if (!isConnected) {
        setIsDemoMode(true);
        setIsConnected(true);
        setMessages(prev => [...prev, {
          type: 'system',
          message: 'Demo mode: Simulated IRC connection',
          timestamp: new Date()
        }]);
        
        // Add some demo users
        setUsers([
          { nick: nickname },
          { nick: 'Alice' },
          { nick: 'Bob' },
          { nick: 'Charlie' },
          { nick: 'DevBot' }
        ]);
        
        // Simulate some initial messages
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'message',
            user: 'DevBot',
            message: `Welcome to #devussy ${nickname}! This is demo mode.`,
            timestamp: new Date()
          }]);
        }, 1000);
        
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'join',
            user: 'Alice',
            message: 'joined the channel',
            timestamp: new Date()
          }]);
        }, 2000);
        
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'message',
            user: 'Alice',
            message: 'Hey everyone! How\'s the coding going?',
            timestamp: new Date()
          }]);
        }, 3000);
      }
    }, 3000);

    return () => {
      clearTimeout(timeoutId);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [nickname, theme, isConnected]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = () => {
    if (!inputMessage.trim()) return;

    if (isDemoMode) {
      // Demo mode: simulate sending a message
      setMessages(prev => [...prev, {
        type: 'message',
        user: nickname,
        message: inputMessage.trim(),
        timestamp: new Date()
      }]);
      
      // Simulate a response after a delay
      if (inputMessage.toLowerCase().includes('hello')) {
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'message',
            user: 'DevBot',
            message: `Hello ${nickname}! 👋`,
            timestamp: new Date()
          }]);
        }, 1000);
      } else if (inputMessage.toLowerCase().includes('help')) {
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'message',
            user: 'DevBot',
            message: 'This is demo mode! Try saying "hello" or ask about the project.',
            timestamp: new Date()
          }]);
        }, 1000);
      }
    } else {
      // Real IRC mode
      if (!wsRef.current || !isConnected) return;

      wsRef.current.send(JSON.stringify({
        cmd: 'PRIVMSG',
        target: '#devussy',
        message: inputMessage.trim()
      }));

      // Add our own message to the chat
      setMessages(prev => [...prev, {
        type: 'message',
        user: nickname,
        message: inputMessage.trim(),
        timestamp: new Date()
      }]);
    }

    setInputMessage('');
  };

  const changeNickname = () => {
    if (!tempNick.trim()) return;
    
    setNickname(tempNick.trim());
    localStorage.setItem('irc-nickname', tempNick.trim());
    setShowNickChange(false);
    setTempNick('');
    
    if (isDemoMode) {
      // Demo mode: show nickname change message
      setMessages(prev => [...prev, {
        type: 'system',
        message: `Nickname changed to ${tempNick.trim()}`,
        timestamp: new Date()
      }]);
    } else if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify({
        cmd: 'NICK',
        nick: tempNick.trim()
      }));
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessage = (msg: IrcMessage, index: number) => {
    const time = formatTime(msg.timestamp);
    
    switch (msg.type) {
      case 'message':
        return (
          <div key={index} className="flex gap-2 py-1">
            <span className="text-xs text-gray-500 font-mono">{time}</span>
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">{msg.user}:</span>
            <span className="text-sm flex-1">{msg.message}</span>
          </div>
        );
        
      case 'join':
        return (
          <div key={index} className="flex gap-2 py-1 text-green-600 dark:text-green-400">
            <span className="text-xs text-gray-500 font-mono">{time}</span>
            <span className="text-sm">→ {msg.user} {msg.message}</span>
          </div>
        );
        
      case 'part':
        return (
          <div key={index} className="flex gap-2 py-1 text-red-600 dark:text-red-400">
            <span className="text-xs text-gray-500 font-mono">{time}</span>
            <span className="text-sm">← {msg.user} {msg.message}</span>
          </div>
        );
        
      case 'system':
        return (
          <div key={index} className="flex gap-2 py-1 text-gray-600 dark:text-gray-400 italic">
            <span className="text-xs text-gray-500 font-mono">{time}</span>
            <span className="text-sm">* {msg.message}</span>
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          <h2 className="text-lg font-semibold">#devussy</h2>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          {isDemoMode && (
            <span className="text-xs bg-yellow-500 text-black px-2 py-1 rounded font-medium">
              DEMO MODE
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {nickname}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setShowNickChange(true);
              setTempNick(nickname);
            }}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Nick Change Dialog */}
      {showNickChange && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-80">
            <CardHeader>
              <CardTitle>Change Nickname</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                value={tempNick}
                onChange={(e) => setTempNick(e.target.value)}
                placeholder="Enter new nickname"
                maxLength={30}
              />
              <div className="flex gap-2">
                <Button onClick={changeNickname} disabled={!tempNick.trim()}>
                  Change
                </Button>
                <Button variant="outline" onClick={() => setShowNickChange(false)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          <ScrollArea className="flex-1 border rounded-lg p-3">
            <div className="space-y-1">
              {messages.map(renderMessage)}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
          
          {/* Input Area */}
          <div className="flex gap-2 mt-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={isConnected ? "Type a message..." : "Connecting..."}
              disabled={!isConnected}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />
            <Button onClick={sendMessage} disabled={!isConnected || !inputMessage.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* User List */}
        <div className="w-48 border rounded-lg p-3">
          <div className="flex items-center gap-2 mb-3">
            <Users className="h-4 w-4" />
            <span className="text-sm font-medium">Users ({users.length})</span>
          </div>
          <ScrollArea className="h-64">
            <div className="space-y-1">
              {users.map((user, index) => (
                <div key={index} className="text-sm text-gray-600 dark:text-gray-400">
                  {user.nick}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
};
