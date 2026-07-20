"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Search, Sparkles, Filter, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { EventCard } from "@/components/cards/EventCard";
import { searchService, eventsService } from "@/services";
import { Event, EventListResponse } from "@/types";

const PLATFORMS = [
  "unstop", "devfolio", "hackerearth", "hack2skill", "devpost",
  "kaggle", "mlh", "github", "codeforces", "codechef",
  "atcoder", "gsoc", "gssoc", "google", "microsoft", "ieee",
];

const EVENT_TYPES = [
  "hackathon", "contest", "internship", "workshop",
  "competition", "quiz", "open_source", "hiring", "conference",
];

const SEARCH_TYPES = [
  { value: "hybrid", label: "🔀 Hybrid" },
  { value: "keyword", label: "🔤 Keyword" },
  { value: "semantic", label: "🧠 Semantic" },
  { value: "ai", label: "✨ AI" },
];

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [searchType, setSearchType] = useState("hybrid");
  const [platform, setPlatform] = useState<string>("");
  const [eventType, setEventType] = useState<string>("");
  const [isRemote, setIsRemote] = useState<boolean | undefined>(undefined);
  const [isFree, setIsFree] = useState<boolean | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  // Debounce query
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 400);
    return () => clearTimeout(timer);
  }, [query]);

  const isSearching = debouncedQuery.trim().length > 0;

  const { data: searchResult, isLoading: searchLoading } = useQuery({
    queryKey: ["search", debouncedQuery, searchType, page],
    queryFn: () => searchService.search({
      query: debouncedQuery,
      search_type: searchType as any,
      page,
      page_size: 20,
    }),
    enabled: isSearching,
  });

  const { data: browseResult, isLoading: browseLoading } = useQuery({
    queryKey: ["events-browse", platform, eventType, isRemote, isFree, page],
    queryFn: () => eventsService.listEvents({
      page,
      page_size: 20,
      platform: platform || undefined,
      event_type: eventType || undefined,
      is_remote: isRemote,
      is_free: isFree,
      sort_by: "ai_score",
    }),
    enabled: !isSearching,
  });

  const events: Event[] = isSearching
    ? searchResult?.results || []
    : browseResult?.items || [];
  const total = isSearching ? searchResult?.total || 0 : browseResult?.total || 0;
  const totalPages = browseResult?.total_pages || 1;
  const isLoading = searchLoading || browseLoading;

  const clearFilters = () => {
    setPlatform("");
    setEventType("");
    setIsRemote(undefined);
    setIsFree(undefined);
    setQuery("");
  };

  const activeFiltersCount = [platform, eventType, isRemote, isFree].filter(Boolean).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-1">Search Opportunities</h1>
        <p className="text-muted-foreground">
          Find hackathons, internships, contests across 15+ platforms
        </p>
      </div>

      {/* Search bar */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='Try: "AI hackathons", "Google internship", "remote free contests"...'
            className="pl-12 h-12 bg-secondary/30 border-border text-base"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <Select value={searchType} onValueChange={(v: string | null) => setSearchType(v || "")}>
          <SelectTrigger className="w-40 h-12 bg-secondary/30 border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SEARCH_TYPES.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          className="h-12 gap-2 relative"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="w-4 h-4" />
          Filters
          {activeFiltersCount > 0 && (
            <span className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-primary text-white text-xs flex items-center justify-center">
              {activeFiltersCount}
            </span>
          )}
        </Button>
      </div>

      {/* AI hint */}
      {searchType === "ai" && (
        <div className="flex items-center gap-2 px-4 py-3 glass rounded-xl border border-primary/20 text-sm text-primary">
          <Sparkles className="w-4 h-4 shrink-0" />
          <span>AI mode interprets natural language. Try: "Show me free web3 hackathons in India" or "Competitions ending this week"</span>
        </div>
      )}

      {/* Filters panel */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="glass rounded-2xl p-5 border border-border/50 space-y-4"
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Filters</h3>
            {activeFiltersCount > 0 && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="text-xs text-muted-foreground">
                Clear all
              </Button>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-xs text-muted-foreground mb-2 block">Platform</Label>
              <Select value={platform} onValueChange={(v: string | null) => setPlatform(v || "")}>
                <SelectTrigger className="h-9 bg-secondary/30 text-sm">
                  <SelectValue placeholder="All platforms" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All platforms</SelectItem>
                  {PLATFORMS.map((p) => (
                    <SelectItem key={p} value={p}>{p}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-xs text-muted-foreground mb-2 block">Event Type</Label>
              <Select value={eventType} onValueChange={(v: string | null) => setEventType(v || "")}>
                <SelectTrigger className="h-9 bg-secondary/30 text-sm">
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All types</SelectItem>
                  {EVENT_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>{t.replace("_", " ")}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-3">
              <Switch
                id="remote"
                checked={isRemote === true}
                onCheckedChange={(v) => setIsRemote(v ? true : undefined)}
              />
              <Label htmlFor="remote" className="text-sm cursor-pointer">Remote Only</Label>
            </div>

            <div className="flex items-center gap-3">
              <Switch
                id="free"
                checked={isFree === true}
                onCheckedChange={(v) => setIsFree(v ? true : undefined)}
              />
              <Label htmlFor="free" className="text-sm cursor-pointer">Free Only</Label>
            </div>
          </div>
        </motion.div>
      )}

      {/* AI explanation */}
      {searchResult?.ai_explanation && (
        <div className="flex items-start gap-2 px-4 py-3 glass rounded-xl border border-primary/20 text-sm">
          <Sparkles className="w-4 h-4 text-primary mt-0.5 shrink-0" />
          <span className="text-muted-foreground">{searchResult.ai_explanation}</span>
        </div>
      )}

      {/* Results header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground text-sm">
            {isLoading ? "Searching..." : `${total.toLocaleString()} opportunities found`}
          </span>
          {isSearching && !isLoading && (
            <Badge variant="outline" className="text-xs">
              Query: &quot;{debouncedQuery}&quot;
            </Badge>
          )}
        </div>
        {!isSearching && totalPages > 1 && (
          <div className="flex items-center gap-2 text-sm">
            <Button
              variant="ghost"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
            >
              Previous
            </Button>
            <span className="text-muted-foreground">Page {page} of {totalPages}</span>
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage(p => p + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </div>

      {/* Results grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass rounded-2xl h-64 skeleton-loading" />
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="glass rounded-2xl p-16 text-center border border-border/50">
          <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No results found</h3>
          <p className="text-muted-foreground text-sm">
            {isSearching
              ? `No events match "${debouncedQuery}". Try different keywords or AI search mode.`
              : "No events match your filters. Try clearing some filters."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {events.map((event, i) => (
            <EventCard key={event.id} event={event} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
