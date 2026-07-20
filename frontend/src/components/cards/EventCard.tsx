"use client";

import { motion } from "framer-motion";
import { format, formatDistanceToNow } from "date-fns";
import {
  Bookmark, BookmarkCheck, ExternalLink, Calendar,
  Trophy, MapPin, Users, Star, Clock, Building2
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Event } from "@/types";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { eventsService } from "@/services";
import { toast } from "sonner";

interface EventCardProps {
  event: Event;
  index?: number;
  onSaveToggle?: () => void;
}

const PLATFORM_COLORS: Record<string, string> = {
  unstop: "text-amber-400",
  devfolio: "text-blue-400",
  hackerearth: "text-purple-400",
  codeforces: "text-red-400",
  codechef: "text-orange-400",
  kaggle: "text-cyan-400",
  devpost: "text-sky-400",
  google: "text-blue-400",
  microsoft: "text-blue-300",
  mlh: "text-red-400",
  gsoc: "text-yellow-400",
  gssoc: "text-green-400",
  github: "text-slate-300",
  ieee: "text-blue-500",
};

const TYPE_STYLES: Record<string, string> = {
  hackathon: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  contest: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  internship: "bg-green-500/20 text-green-300 border-green-500/30",
  workshop: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  competition: "bg-red-500/20 text-red-300 border-red-500/30",
  quiz: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  open_source: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  hiring: "bg-pink-500/20 text-pink-300 border-pink-500/30",
  conference: "bg-orange-500/20 text-orange-300 border-orange-500/30",
};

function AIScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? "text-green-400" : score >= 60 ? "text-yellow-400" : "text-red-400";
  return (
    <div className={cn("flex items-center gap-1 text-xs font-semibold", color)}>
      <Star className="w-3 h-3 fill-current" />
      {score.toFixed(0)}
    </div>
  );
}

export function EventCard({ event, index = 0, onSaveToggle }: EventCardProps) {
  const [isSaved, setIsSaved] = useState(event.is_saved ?? false);
  const [saving, setSaving] = useState(false);

  const deadline = event.registration_deadline
    ? new Date(event.registration_deadline)
    : null;
  const isExpired = deadline && deadline < new Date();
  const daysLeft = deadline
    ? Math.ceil((deadline.getTime() - Date.now()) / 86400000)
    : null;

  const toggleSave = async (e: React.MouseEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (isSaved) {
        await eventsService.unsaveEvent(event.id);
        setIsSaved(false);
        toast.success("Removed from saved");
      } else {
        await eventsService.saveEvent(event.id);
        setIsSaved(true);
        toast.success("Saved!");
      }
      onSaveToggle?.();
    } catch {
      toast.error("Failed to update saved status");
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="group glass rounded-2xl p-5 border border-border/50 hover:border-primary/30 transition-all glow-hover cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span
              className={cn(
                "text-xs font-semibold uppercase tracking-wider",
                PLATFORM_COLORS[event.platform] || "text-primary"
              )}
            >
              {event.platform}
            </span>
            <Badge
              variant="outline"
              className={cn(
                "text-xs border capitalize",
                TYPE_STYLES[event.event_type] || TYPE_STYLES.hackathon
              )}
            >
              {event.event_type.replace("_", " ")}
            </Badge>
            {event.is_free && (
              <Badge variant="outline" className="text-xs border-green-500/30 text-green-400 bg-green-500/10">
                Free
              </Badge>
            )}
            {event.is_remote && (
              <Badge variant="outline" className="text-xs border-blue-500/30 text-blue-400 bg-blue-500/10">
                Remote
              </Badge>
            )}
          </div>
          <h3 className="font-semibold text-base leading-tight group-hover:text-primary transition-colors line-clamp-2">
            {event.title}
          </h3>
        </div>
        <AIScoreBadge score={event.ai_score} />
      </div>

      {/* Summary */}
      {event.short_summary && (
        <p className="text-muted-foreground text-sm leading-relaxed line-clamp-2 mb-3">
          {event.short_summary}
        </p>
      )}

      {/* Meta */}
      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground mb-4">
        {event.prize && (
          <div className="flex items-center gap-1 text-amber-400">
            <Trophy className="w-3.5 h-3.5" />
            <span className="font-medium">{event.prize}</span>
          </div>
        )}
        {deadline && (
          <div className={cn("flex items-center gap-1", isExpired ? "text-destructive" : daysLeft && daysLeft <= 3 ? "text-orange-400 font-semibold" : "")}>
            <Clock className="w-3.5 h-3.5" />
            <span>
              {isExpired
                ? "Expired"
                : daysLeft === 0
                ? "Due today!"
                : `${daysLeft}d left`}
            </span>
          </div>
        )}
        {event.location && (
          <div className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            <span>{event.location}</span>
          </div>
        )}
        {event.participant_count > 0 && (
          <div className="flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            <span>{event.participant_count.toLocaleString()}</span>
          </div>
        )}
        {event.organizer && (
          <div className="flex items-center gap-1">
            <Building2 className="w-3.5 h-3.5" />
            <span className="truncate max-w-[120px]">{event.organizer}</span>
          </div>
        )}
      </div>

      {/* Tags */}
      {event.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {event.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 rounded-md bg-secondary/50 text-xs text-muted-foreground"
            >
              #{tag}
            </span>
          ))}
          {event.tags.length > 4 && (
            <span className="text-xs text-muted-foreground">+{event.tags.length - 4}</span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-border/30">
        <a
          href={event.registration_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Register Now
        </a>

        <button
          onClick={toggleSave}
          disabled={saving}
          className={cn(
            "flex items-center gap-1.5 text-xs transition-colors",
            isSaved ? "text-primary" : "text-muted-foreground hover:text-foreground"
          )}
        >
          {isSaved ? (
            <BookmarkCheck className="w-4 h-4 fill-primary" />
          ) : (
            <Bookmark className="w-4 h-4" />
          )}
          {isSaved ? "Saved" : "Save"}
        </button>
      </div>
    </motion.div>
  );
}
