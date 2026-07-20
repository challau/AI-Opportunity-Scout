"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BookmarkCheck, Bookmark } from "lucide-react";
import { EventCard } from "@/components/cards/EventCard";
import { eventsService } from "@/services";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function SavedPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["saved-events", page],
    queryFn: () => eventsService.getSavedEvents(page),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BookmarkCheck className="w-7 h-7 text-primary" />
            Saved Events
          </h1>
          <p className="text-muted-foreground mt-1">
            {data?.total || 0} events saved to your list
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass rounded-2xl h-64 skeleton-loading" />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="glass rounded-2xl p-16 text-center border border-border/50">
          <Bookmark className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No saved events yet</h3>
          <p className="text-muted-foreground text-sm">
            Save events from the search or dashboard to find them here.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.items.map((event, i) => (
              <EventCard
                key={event.id}
                event={{ ...event, is_saved: true }}
                index={i}
                onSaveToggle={refetch}
              />
            ))}
          </div>

          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-4">
              <Button variant="outline" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                Previous
              </Button>
              <span className="text-muted-foreground text-sm">
                Page {page} of {data.total_pages}
              </span>
              <Button variant="outline" disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)}>
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
