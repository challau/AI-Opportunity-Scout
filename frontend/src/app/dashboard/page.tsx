"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Trophy, Clock, Star, Zap, TrendingUp, Target,
  Bell, BookmarkCheck, Calendar, ArrowRight, Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EventCard } from "@/components/cards/EventCard";
import { eventsService, aiService, notificationsService } from "@/services";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

function StatCard({
  icon: Icon,
  label,
  value,
  color,
  delay = 0,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="glass rounded-2xl p-5 border border-border/50 glow-hover"
    >
      <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center mb-3`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const { data: todayEvents = [], isLoading: todayLoading } = useQuery({
    queryKey: ["today-events"],
    queryFn: eventsService.getTodayEvents,
  });

  const { data: upcomingDeadlines = [], isLoading: deadlineLoading } = useQuery({
    queryKey: ["upcoming-deadlines"],
    queryFn: () => eventsService.getUpcomingDeadlines(7),
  });

  const { data: recommendations = [], isLoading: recLoading } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => aiService.getRecommendations(6),
  });

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsService.getNotifications({ page: 1, unread_only: true }),
  });

  const { data: savedEvents } = useQuery({
    queryKey: ["saved-events"],
    queryFn: () => eventsService.getSavedEvents(),
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold">
            Welcome back! <span className="gradient-text">🚀</span>
          </h1>
          <p className="text-muted-foreground mt-1">
            Your personalized opportunity feed — new events every 6 hours, digests to your inbox
          </p>
        </div>
        <Link href="/search">
          <Button className="gradient-primary text-white border-0 gap-2">
            <Zap className="w-4 h-4" />
            Find Opportunities
          </Button>
        </Link>
      </motion.div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Star} label="Today's Events" value={todayEvents.length} color="gradient-primary" delay={0} />
        <StatCard icon={Clock} label="Upcoming Deadlines" value={upcomingDeadlines.length} color="bg-orange-500" delay={0.05} />
        <StatCard icon={BookmarkCheck} label="Saved Events" value={savedEvents?.total || 0} color="bg-green-500" delay={0.1} />
        <StatCard icon={Bell} label="Unread Alerts" value={notifications.length} color="bg-violet-500" delay={0.15} />
      </div>

      {/* Today's opportunities */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <h2 className="text-xl font-semibold">Today&apos;s Opportunities</h2>
            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
              {todayEvents.length} new
            </Badge>
          </div>
          <Link href="/search">
            <Button variant="ghost" size="sm" className="gap-1 text-muted-foreground hover:text-foreground">
              View All <ArrowRight className="w-3 h-3" />
            </Button>
          </Link>
        </div>

        {todayLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="glass rounded-2xl h-64 skeleton-loading" />
            ))}
          </div>
        ) : todayEvents.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center border border-border/50">
            <Zap className="w-12 h-12 text-primary mx-auto mb-3 animate-pulse" />
            <p className="text-muted-foreground">Crawlers are running — check back soon!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {todayEvents.slice(0, 6).map((event, i) => (
              <EventCard key={event.id} event={event} index={i} />
            ))}
          </div>
        )}
      </section>

      {/* Upcoming deadlines */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-orange-400" />
            <h2 className="text-xl font-semibold">Upcoming Deadlines</h2>
          </div>
        </div>

        {deadlineLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="glass rounded-xl h-16 skeleton-loading" />
            ))}
          </div>
        ) : upcomingDeadlines.length === 0 ? (
          <div className="glass rounded-xl p-6 text-center text-muted-foreground">
            No upcoming deadlines in the next 7 days
          </div>
        ) : (
          <div className="space-y-3">
            {upcomingDeadlines.slice(0, 5).map((event, i) => {
              const deadline = new Date(event.registration_deadline!);
              const daysLeft = Math.ceil((deadline.getTime() - Date.now()) / 86400000);
              return (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="glass rounded-xl p-4 border border-border/50 flex items-center gap-4 hover:border-orange-400/30 transition-all"
                >
                  <div
                    className={`w-12 h-12 rounded-xl flex flex-col items-center justify-center text-white shrink-0 ${
                      daysLeft <= 1 ? "bg-red-500" : daysLeft <= 3 ? "bg-orange-500" : "bg-amber-500"
                    }`}
                  >
                    <div className="text-lg font-bold leading-none">{daysLeft}</div>
                    <div className="text-[9px]">days</div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{event.title}</div>
                    <div className="text-sm text-muted-foreground">
                      {event.platform} · {event.event_type} ·{" "}
                      {deadline.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </div>
                  </div>
                  <a
                    href={event.registration_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button size="sm" variant="outline" className="shrink-0 text-xs">
                      Register
                    </Button>
                  </a>
                </motion.div>
              );
            })}
          </div>
        )}
      </section>

      {/* AI Recommendations */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            <h2 className="text-xl font-semibold">AI Recommendations</h2>
            <Badge className="bg-primary/20 text-primary border-primary/30 text-xs">
              Personalized
            </Badge>
          </div>
          <Link href="/search">
            <Button variant="ghost" size="sm" className="gap-1 text-muted-foreground">
              More <ArrowRight className="w-3 h-3" />
            </Button>
          </Link>
        </div>

        {recLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="glass rounded-2xl h-64 skeleton-loading" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {recommendations.map((event, i) => (
              <EventCard key={event.id} event={event} index={i} />
            ))}
          </div>
        )}
      </section>

      {/* Recent Notifications */}
      {notifications.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Bell className="w-5 h-5 text-violet-400" />
            <h2 className="text-xl font-semibold">Recent Alerts</h2>
            <Badge className="bg-violet-500/20 text-violet-300 border-violet-500/30 text-xs">
              {notifications.length} unread
            </Badge>
          </div>
          <div className="space-y-2">
            {notifications.slice(0, 5).map((notif, i) => (
              <motion.div
                key={notif.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="glass rounded-xl p-4 border border-border/50 flex items-center gap-3"
              >
                <div className="w-2 h-2 rounded-full bg-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{notif.title}</div>
                  <div className="text-xs text-muted-foreground">{notif.body}</div>
                </div>
                <div className="text-xs text-muted-foreground shrink-0">
                  {formatDistanceToNow(new Date(notif.created_at), { addSuffix: true })}
                </div>
              </motion.div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
