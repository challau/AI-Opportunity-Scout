"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, User, Bot, Loader2, X, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { EventCard } from "@/components/cards/EventCard";
import { aiService } from "@/services";
import { ChatMessage, Event } from "@/types";
import { cn } from "@/lib/utils";

const SUGGESTED_PROMPTS = [
  "Find AI hackathons with prize money",
  "Show me free remote internships",
  "What coding contests are ending this week?",
  "Recommend events for a Python developer",
  "Best GSoC organizations for beginners",
];

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  suggestedEvents?: Event[];
  timestamp: Date;
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hey! 👋 I'm your AI Opportunity Scout assistant. Ask me anything about hackathons, internships, coding contests, or open-source programs. I can search across 15+ platforms and give you personalized recommendations!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const history = useRef<Array<{ role: string; content: string }>>([]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await aiService.chat({
        message: text,
        conversation_history: history.current,
      });

      history.current.push({ role: "user", content: text });
      history.current.push({ role: "assistant", content: response.message });

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.message,
        suggestedEvents: response.suggested_events,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I had trouble connecting. Please check your API keys and try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 shrink-0">
        <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center animate-pulse-glow">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">AI Opportunity Assistant</h1>
          <p className="text-muted-foreground text-sm">Ask me anything about tech opportunities</p>
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-green-400">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          Online
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2 mb-4">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn("flex gap-3", msg.role === "user" ? "flex-row-reverse" : "flex-row")}
            >
              {/* Avatar */}
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5",
                  msg.role === "assistant" ? "gradient-primary" : "bg-secondary"
                )}
              >
                {msg.role === "assistant" ? (
                  <Bot className="w-4 h-4 text-white" />
                ) : (
                  <User className="w-4 h-4 text-foreground" />
                )}
              </div>

              {/* Bubble */}
              <div className={cn("max-w-[75%]", msg.role === "user" ? "items-end" : "items-start")}>
                <div
                  className={cn(
                    "px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap",
                    msg.role === "assistant"
                      ? "glass border border-border/50 text-foreground"
                      : "gradient-primary text-white"
                  )}
                >
                  {msg.content}
                </div>

                {/* Suggested events */}
                {msg.suggestedEvents && msg.suggestedEvents.length > 0 && (
                  <div className="mt-3 space-y-3">
                    <p className="text-xs text-muted-foreground px-1">Related opportunities:</p>
                    {msg.suggestedEvents.slice(0, 3).map((event, i) => (
                      <EventCard key={event.id} event={event} index={i} />
                    ))}
                  </div>
                )}

                <div className="text-xs text-muted-foreground mt-1 px-1">
                  {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
            </motion.div>
          ))}

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="glass border border-border/50 px-4 py-3 rounded-2xl">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-2 h-2 rounded-full bg-primary animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={scrollRef} />
      </div>

      {/* Suggested prompts (show only at start) */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mb-3 shrink-0">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => sendMessage(prompt)}
              className="px-3 py-1.5 text-xs glass rounded-full border border-border/50 text-muted-foreground hover:text-foreground hover:border-primary/30 transition-all"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3 shrink-0">
        <Input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about hackathons, internships, contests..."
          className="flex-1 h-12 bg-secondary/30 border-border focus:border-primary/50 text-sm"
          disabled={loading}
        />
        <Button
          type="submit"
          disabled={loading || !input.trim()}
          className="h-12 px-5 gradient-primary text-white border-0 glow-hover"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </Button>
      </form>
    </div>
  );
}
