"use client";

import { Bell, Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { User } from "@/types";
import { useRouter } from "next/navigation";

interface TopbarProps {
  user: User | null;
}

export function Topbar({ user }: TopbarProps) {
  const router = useRouter();

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const q = (e.currentTarget.elements.namedItem("q") as HTMLInputElement).value;
    if (q.trim()) router.push(`/search?q=${encodeURIComponent(q)}`);
  };

  return (
    <header className="h-16 border-b border-border/50 px-6 flex items-center gap-4 bg-background/80 backdrop-blur-sm shrink-0">
      <form onSubmit={handleSearch} className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            name="q"
            placeholder="Search hackathons, internships, contests..."
            className="pl-9 bg-secondary/30 border-border/50 focus:border-primary/50 h-9"
          />
        </div>
      </form>

      <div className="flex items-center gap-2 ml-auto">
        <Link href="/chatbot">
          <Button variant="ghost" size="sm" className="gap-2 text-primary hidden sm:flex">
            <Sparkles className="w-4 h-4" />
            AI Chat
          </Button>
        </Link>

        <Link href="/notifications">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="w-5 h-5" />
          </Button>
        </Link>

        <Link href="/profile">
          <Avatar className="w-8 h-8 cursor-pointer ring-2 ring-primary/20 hover:ring-primary/50 transition-all">
            <AvatarImage src={user?.avatar_url} />
            <AvatarFallback className="gradient-primary text-white text-sm">
              {user?.full_name?.charAt(0) || "U"}
            </AvatarFallback>
          </Avatar>
        </Link>
      </div>
    </header>
  );
}
