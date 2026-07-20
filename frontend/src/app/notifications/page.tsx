"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bell, CheckCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { notificationsService } from "@/services";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";

const TYPE_COLORS: Record<string, string> = {
  new_event: "bg-primary/20 text-primary border-primary/30",
  deadline_reminder: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  info: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  success: "bg-green-500/20 text-green-300 border-green-500/30",
};

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data: notifications = [], isLoading } = useQuery({
    queryKey: ["all-notifications"],
    queryFn: () => notificationsService.getNotifications({ page: 1 }),
  });

  const markAllMutation = useMutation({
    mutationFn: notificationsService.markAllRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["all-notifications"] });
      toast.success("All notifications marked as read");
    },
  });

  const markReadMutation = useMutation({
    mutationFn: notificationsService.markAsRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["all-notifications"] }),
  });

  const unread = notifications.filter((n) => !n.is_read);

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bell className="w-7 h-7 text-primary" />
            Notifications
          </h1>
          <p className="text-muted-foreground mt-1">
            {unread.length} unread · {notifications.length} total
          </p>
        </div>
        {unread.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
            className="gap-2"
          >
            {markAllMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCheck className="w-4 h-4" />}
            Mark all read
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass rounded-xl h-20 skeleton-loading" />
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="glass rounded-2xl p-16 text-center border border-border/50">
          <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No notifications yet</h3>
          <p className="text-muted-foreground text-sm">
            We'll notify you when new opportunities match your interests.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((notif, i) => (
            <motion.div
              key={notif.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className={`glass rounded-xl p-4 border transition-all cursor-pointer ${
                notif.is_read ? "border-border/30 opacity-70" : "border-primary/20"
              }`}
              onClick={() => !notif.is_read && markReadMutation.mutate(notif.id)}
            >
              <div className="flex items-start gap-3">
                {!notif.is_read && (
                  <div className="w-2 h-2 rounded-full bg-primary shrink-0 mt-2" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">{notif.title}</span>
                    <Badge
                      variant="outline"
                      className={`text-xs ${TYPE_COLORS[notif.type] || TYPE_COLORS.info}`}
                    >
                      {notif.type.replace("_", " ")}
                    </Badge>
                  </div>
                  {notif.body && (
                    <p className="text-sm text-muted-foreground line-clamp-2">{notif.body}</p>
                  )}
                </div>
                <div className="text-xs text-muted-foreground shrink-0">
                  {formatDistanceToNow(new Date(notif.created_at), { addSuffix: true })}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
