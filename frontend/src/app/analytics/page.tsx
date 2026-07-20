"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BarChart3, Trophy, Globe, Clock } from "lucide-react";
import { eventsService, adminService } from "@/services";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from "recharts";

export default function AnalyticsPage() {
  const { data: platformStats = [] } = useQuery({
    queryKey: ["analytics-platform"],
    queryFn: adminService.getEventsByPlatform,
  });

  const { data: typeStats = [] } = useQuery({
    queryKey: ["analytics-type"],
    queryFn: adminService.getEventsByType,
  });

  const CHART_TOOLTIP_STYLE = {
    contentStyle: { background: "#1a1a2e", border: "1px solid #3a3a5c", borderRadius: 8, fontSize: 12 }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <BarChart3 className="w-7 h-7 text-primary" />
          Analytics
        </h1>
        <p className="text-muted-foreground mt-1">Platform insights and opportunity trends</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass rounded-2xl p-6 border border-border/50">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            Events by Platform
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={platformStats} barSize={18}>
              <XAxis dataKey="platform" tick={{ fill: "#64748b", fontSize: 10 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
              <Tooltip {...CHART_TOOLTIP_STYLE} />
              <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="glass rounded-2xl p-6 border border-border/50">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-primary" />
            Events by Type
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={typeStats} barSize={18} layout="vertical">
              <XAxis type="number" tick={{ fill: "#64748b", fontSize: 10 }} />
              <YAxis dataKey="type" type="category" tick={{ fill: "#64748b", fontSize: 10 }} width={80} />
              <Tooltip {...CHART_TOOLTIP_STYLE} />
              <Bar dataKey="count" fill="#a78bfa" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Top platforms table */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="glass rounded-2xl p-6 border border-border/50">
        <h3 className="font-semibold mb-4">Platform Breakdown</h3>
        <div className="space-y-3">
          {platformStats.sort((a: any, b: any) => b.count - a.count).slice(0, 10).map((p: any, i: number) => {
            const maxCount = platformStats[0]?.count || 1;
            const pct = Math.round((p.count / maxCount) * 100);
            return (
              <div key={p.platform} className="flex items-center gap-4">
                <div className="w-24 text-sm text-muted-foreground capitalize truncate">{p.platform}</div>
                <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ delay: i * 0.05, duration: 0.5 }}
                    className="h-full gradient-primary rounded-full"
                  />
                </div>
                <div className="w-12 text-sm text-right font-medium">{p.count}</div>
              </div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
