"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Search, BookmarkCheck, Bell, User,
  BarChart3, MessageSquare, Settings, Shield, LogOut,
  Rocket, ChevronLeft, Menu, X, Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { clearTokens } from "@/lib/api";
import { notificationsService } from "@/services";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/search", icon: Search, label: "Search" },
  { href: "/saved", icon: BookmarkCheck, label: "Saved" },
  { href: "/chatbot", icon: MessageSquare, label: "AI Chat" },
  { href: "/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/profile", icon: User, label: "Profile" },
];

const BOTTOM_ITEMS = [
  { href: "/admin", icon: Shield, label: "Admin" },
];

interface SidebarProps {
  isCollapsed: boolean;
  onCollapse: (v: boolean) => void;
}

export function Sidebar({ isCollapsed, onCollapse }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    notificationsService.getUnreadCount().then(setUnreadCount).catch(() => {});
    const interval = setInterval(() => {
      notificationsService.getUnreadCount().then(setUnreadCount).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    clearTokens();
    router.push("/login");
  };

  return (
    <motion.aside
      animate={{ width: isCollapsed ? 72 : 240 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
      className="sidebar flex flex-col h-full overflow-hidden shrink-0"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-sidebar-border">
        <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center shrink-0">
          <Rocket className="w-5 h-5 text-white" />
        </div>
        <AnimatePresence>
          {!isCollapsed && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="font-bold text-sm gradient-text whitespace-nowrap"
            >
              AI Opportunity Scout
            </motion.span>
          )}
        </AnimatePresence>
        <button
          onClick={() => onCollapse(!isCollapsed)}
          className="ml-auto text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          <ChevronLeft
            className={cn("w-4 h-4 transition-transform", isCollapsed && "rotate-180")}
          />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: isCollapsed ? 0 : 3 }}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer",
                  isActive
                    ? "gradient-primary text-white shadow-lg"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                )}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="whitespace-nowrap flex-1"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
                {item.href === "/notifications" && unreadCount > 0 && !isCollapsed && (
                  <Badge className="ml-auto bg-primary/20 text-primary border-primary/30 text-xs">
                    {unreadCount}
                  </Badge>
                )}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-2 pb-4 space-y-1 border-t border-sidebar-border pt-4">
        {BOTTOM_ITEMS.map((item) => (
          <Link key={item.href} href={item.href}>
            <div className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-all cursor-pointer",
              pathname.startsWith(item.href) && "text-foreground bg-secondary/50"
            )}>
              <item.icon className="w-5 h-5 shrink-0" />
              {!isCollapsed && <span className="whitespace-nowrap">{item.label}</span>}
            </div>
          </Link>
        ))}

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all w-full cursor-pointer"
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!isCollapsed && <span className="whitespace-nowrap">Sign Out</span>}
        </button>
      </div>
    </motion.aside>
  );
}
