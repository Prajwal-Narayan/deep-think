"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Bot, User, Brain, Shield, 
  CheckCircle2, Loader2, ChevronRight, Terminal, AlertCircle
} from 'lucide-react';

// --- Types ---
type Message = {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
};

type PlanStep = {
  id: number;
  title: string;
  tool: string;
  status: 'pending' | 'active' | 'completed';
  logs: string[];
};

export default function GodTierInterface() {
  const [query, setQuery] = useState("");
  const [isResearching, setIsResearching] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'agent',
      content: "Major, I am online. Deep Research Protocol v1 is active. What is your directive?",
      timestamp: new Date()
    }
  ]);
  
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, plan]);

  // --- THE REAL ENGINE (SSE STREAM) ---
  const runResearch = async () => {
    if (!query.trim()) return;

    // 1. Add User Message
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: query, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setIsResearching(true);
    setPlan([]); // Reset Plan
    const currentQuery = query;
    setQuery("");

    try {
      // 2. Open Connection to Python Backend
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery })
      });

      if (!response.ok) throw new Error('Network response was not ok');
      if (!response.body) throw new Error('No body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let activeStepIndex = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (dataStr === '[DONE]') break;
            
            try {
              const event = JSON.parse(dataStr);
              
              // --- HANDLE GRAPH EVENTS ---
              
              // 1. PLANNER: Receive the Master Plan
              if (event.node === "planner" && event.data.plan) {
                const newPlan = event.data.plan.map((s: any) => ({
                  ...s,
                  status: 'pending',
                  logs: []
                }));
                // Mark first step as active immediately
                if (newPlan.length > 0) newPlan[0].status = 'active';
                setPlan(newPlan);
              }

              // 2. EXECUTOR: Step Finished
              if (event.node === "executor") {
                setPlan(prev => prev.map((step, idx) => {
                   if (idx === activeStepIndex) {
                     return { ...step, status: 'completed', logs: [...step.logs, "Execution complete. Data retrieved."] };
                   }
                   if (idx === activeStepIndex + 1) {
                     return { ...step, status: 'active' };
                   }
                   return step;
                }));
                activeStepIndex++;
              }

              // 3. REPORTER: Final Answer
              if (event.node === "reporter" && event.data.final_answer) {
                 const agentMsg: Message = {
                    id: Date.now().toString(),
                    role: 'agent',
                    content: event.data.final_answer,
                    timestamp: new Date()
                 };
                 setMessages(prev => [...prev, agentMsg]);
                 setIsResearching(false);
              }

            } catch (e) {
              console.error("Error parsing event:", e);
            }
          }
        }
      }

    } catch (error) {
      console.error("Stream Error:", error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'agent',
        content: "❌ CONNECTION FAILURE: Ensure the Python Backend is running on port 8000.",
        timestamp: new Date()
      }]);
      setIsResearching(false);
    }
  };

  return (
    <div className="flex h-screen bg-black text-gray-100 font-sans overflow-hidden selection:bg-emerald-500/30">
      
      {/* --- LEFT PANEL: THE CHAT --- */}
      <div className="flex-1 flex flex-col relative z-10 border-r border-white/10">
        <header className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-black/50 backdrop-blur-md">
          <div className="flex items-center gap-2 text-emerald-500">
            <Shield className="w-5 h-5" />
            <span className="font-bold tracking-wider text-sm">DEEP RESEARCH v1</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
             <div className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${isResearching ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`}></span>
                {isResearching ? 'PROCESSING' : 'SYSTEM ONLINE'}
             </div>
             <div className="px-2 py-1 rounded bg-white/5 border border-white/10">TIER 1 ACCESS</div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'agent' && (
                <div className="w-8 h-8 rounded bg-emerald-900/20 border border-emerald-500/20 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-emerald-500" />
                </div>
              )}
              <div className={`max-w-[80%] rounded-lg p-4 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user' 
                  ? 'bg-white/10 border border-white/10 text-white' 
                  : 'bg-black border border-white/5 text-gray-300 shadow-2xl'
              }`}>
                {msg.content}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-gray-400" />
                </div>
              )}
            </div>
          ))}
          {isResearching && (
             <div className="flex gap-4">
                <div className="w-8 h-8 rounded bg-emerald-900/20 border border-emerald-500/20 flex items-center justify-center animate-pulse">
                  <Brain className="w-4 h-4 text-emerald-500" />
                </div>
                <div className="flex items-center gap-2 text-xs text-emerald-500/70 mt-2">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Neural Engine is thinking...
                </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-white/10 bg-black/80 backdrop-blur">
          <div className="relative max-w-4xl mx-auto">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runResearch()}
              placeholder="Enter Research Directive..."
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-4 pr-12 text-sm focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all placeholder:text-gray-600"
            />
            <button 
              onClick={runResearch}
              disabled={!query.trim() || isResearching}
              className="absolute right-2 top-2 p-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* --- RIGHT PANEL: THE BRAIN --- */}
      <div className="w-[400px] bg-black/95 border-l border-white/10 flex flex-col hidden md:flex">
        <div className="h-16 border-b border-white/10 flex items-center px-6 gap-2">
          <Brain className="w-4 h-4 text-purple-500" />
          <span className="font-bold text-xs tracking-widest text-gray-400">NEURAL ENGINE STATE</span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {plan.length === 0 ? (
             <div className="h-full flex flex-col items-center justify-center text-gray-700 space-y-4 opacity-50">
               <Terminal className="w-12 h-12" />
               <p className="text-xs font-mono">WAITING FOR PLAN...</p>
             </div>
          ) : (
            plan.map((step, idx) => (
              <div key={idx} className={`
                border rounded-lg p-4 transition-all duration-500
                ${step.status === 'active' ? 'border-emerald-500/50 bg-emerald-500/5 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 
                  step.status === 'completed' ? 'border-white/10 bg-white/5 opacity-60' : 
                  'border-white/5 bg-transparent opacity-30'}
              `}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className={`
                      w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border
                      ${step.status === 'active' ? 'border-emerald-500 text-emerald-500' : 
                        step.status === 'completed' ? 'bg-emerald-500 border-emerald-500 text-black' : 
                        'border-gray-700 text-gray-700'}
                    `}>
                      {step.status === 'completed' ? <CheckCircle2 className="w-3 h-3" /> : idx + 1}
                    </div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-gray-300">
                      {step.title}
                    </span>
                  </div>
                  {step.status === 'active' && <Loader2 className="w-3 h-3 text-emerald-500 animate-spin" />}
                </div>
                
                {/* Tool Badge */}
                <div className="pl-9 mb-2">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase">
                        {step.tool.replace('_', ' ')}
                    </span>
                </div>

                {/* Logs */}
                <div className="pl-9 space-y-1">
                   {step.logs.map((log, i) => (
                      <div key={i} className="flex items-center gap-2 text-[10px] font-mono text-gray-500">
                        <ChevronRight className="w-2 h-2 text-emerald-500/50" />
                        {log}
                      </div>
                   ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}