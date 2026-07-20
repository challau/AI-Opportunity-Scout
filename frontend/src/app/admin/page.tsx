"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  BarChart3, Users, Zap, Database, Clock, TrendingUp,
  RefreshCw, CheckCircle, XCircle, AlertCircle, Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { adminService, aiService } from "@/services";
import { toast } from "sonner";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

const STATUS_ICON = {
  success: CheckCircle,
  failed: XCircle,
  partial: AlertCircle,
  running: Loader2,
};

const STATUS_COLOR = {
  success: "text-green-400",
  failed: "text-red-400",
  partial: "text-yellow-400",
  running: "text-blue-400",
};

const CHART_COLORS = ["#818cf8", "#a78bfa", "#c084fc", "#60a5fa", "#34d399", "#fb923c", "#f472b6", "#22d3ee"];

export default function AdminPage() {
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: adminService.getStats,
    refetchInterval: 30000,
  });

  const { data: crawlerLogs = [], isLoading: logsLoading } = useQuery({
    queryKey: ["crawler-logs"],
    queryFn: () => adminService.getCrawlerLogs(1),
    refetchInterval: 15000,
  });

  const { data: platformStats = [] } = useQuery({
    queryKey: ["events-by-platform"],
    queryFn: adminService.getEventsByPlatform,
  });

  const { data: typeStats = [] } = useQuery({
    queryKey: ["events-by-type"],
    queryFn: adminService.getEventsByType,
  });

  const handleTriggerCrawl = async () => {
    try {
      await aiService.triggerCrawl("all");
      toast.success("Crawl triggered! This may take a few minutes.");
      setTimeout(() => refetchStats(), 3000);
    } catch {
      toast.error("Failed to trigger crawl");
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-primary" />
            Admin Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">Monitor crawlers, users, and platform analytics</p>
        </div>
        <Button
          onClick={handleTriggerCrawl}
          className="gradient-primary text-white border-0 gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Trigger Crawl
        </Button>
      </div>

      {/* Stats cards */}
      {statsLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass rounded-2xl h-28 skeleton-loading" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: Users, label: "Total Users", value: stats?.total_users, color: "bg-violet-500" },
            { icon: Database, label: "Total Events", value: stats?.total_events, color: "gradient-primary" },
            { icon: Zap, label: "Events Today", value: stats?.events_today, color: "bg-green-500" },
            { icon: Clock, label: "Notifications Sent", value: stats?.total_notifications, color: "bg-orange-500" },
          ].map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass rounded-2xl p-5 border border-border/50"
            >
              <div className={`w-10 h-10 rounded-xl ${s.color} flex items-center justify-center mb-3`}>
                <s.icon className="w-5 h-5 text-white" />
              </div>
              <div className="text-2xl font-bold">{s.value?.toLocaleString() ?? "—"}</div>
              <div className="text-sm text-muted-foreground">{s.label}</div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass rounded-2xl p-6 border border-border/50"
        >
          <h3 className="font-semibold mb-4">Events by Platform</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={platformStats} barSize={20}>
              <XAxis dataKey="platform" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "#1a1a2e", border: "1px solid #3a3a5c", borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-6 border border-border/50"
        >
          <h3 className="font-semibold mb-4">Events by Type</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={typeStats}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="count"
                nameKey="type"
              >
                {typeStats.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#1a1a2e", border: "1px solid #3a3a5c", borderRadius: 8, fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {typeStats.map((s, i) => (
              <div key={s.type} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <div className="w-2 h-2 rounded-full" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                {s.type}
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Crawler logs */}
      <section>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-primary" />
          Recent Crawler Runs
        </h2>

        {logsLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="glass rounded-xl h-16 skeleton-loading" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {crawlerLogs.map((log, i) => {
              const StatusIcon = STATUS_ICON[log.status] || AlertCircle;
              return (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="glass rounded-xl p-4 border border-border/50 flex items-center gap-4"
                >
                  <StatusIcon
                    className={`w-5 h-5 shrink-0 ${STATUS_COLOR[log.status]} ${log.status === "running" ? "animate-spin" : ""}`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium capitalize">{log.platform}</span>
                      <Badge
                        variant="outline"
                        className={`text-xs ${STATUS_COLOR[log.status]} border-current bg-current/10`}
                      >
                        {log.status}
                      </Badge>
                    </div>
                    <div className="flex gap-4 text-xs text-muted-foreground">
                      <span>Found: {log.events_found}</span>
                      <span>New: {log.events_new}</span>
                      {log.duration_seconds && <span>Duration: {log.duration_seconds.toFixed(1)}s</span>}
                      {log.error_message && (
                        <span className="text-destructive truncate max-w-xs">{log.error_message}</span>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground shrink-0">
                    {new Date(log.started_at).toLocaleString()}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
