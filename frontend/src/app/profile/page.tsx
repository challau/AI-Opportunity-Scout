"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  User, Bell, Globe, Code2, Upload, FileText,
  CheckCircle, Loader2, Sparkles, Trash2, Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { usersService, authService, resumeService } from "@/services";
import { EventCard } from "@/components/cards/EventCard";

const DOMAINS = [
  "AI/ML", "Web Development", "Mobile Dev", "Data Science", "Blockchain",
  "Cloud", "Cybersecurity", "Open Source", "Hardware/IoT", "Game Dev",
];

const LANGUAGES = [
  "Python", "JavaScript", "TypeScript", "Java", "C++", "Go",
  "Rust", "Ruby", "PHP", "Swift", "Kotlin", "R",
];

const PLATFORMS_LIST = [
  "unstop", "devfolio", "hackerearth", "kaggle", "codeforces",
  "devpost", "mlh", "google", "microsoft", "gsoc",
];

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<any>(null);
  const [selectedDomains, setSelectedDomains] = useState<string[]>([]);
  const [selectedLangs, setSelectedLangs] = useState<string[]>([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [resumeMatchResults, setResumeMatchResults] = useState<any[]>([]);
  const [matchLoading, setMatchLoading] = useState(false);

  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: usersService.getProfile,
  });

  const { data: resumes = [] } = useQuery({
    queryKey: ["my-resumes"],
    queryFn: resumeService.getMyResumes,
  });

  useEffect(() => {
    authService.getMe().then(setUser).catch(() => {});
  }, []);

  useEffect(() => {
    if (profile) {
      setSelectedDomains(profile.interested_domains || []);
      setSelectedLangs(profile.programming_languages || []);
      setSelectedPlatforms(profile.preferred_platforms || []);
    }
  }, [profile]);

  const updateMutation = useMutation({
    mutationFn: usersService.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Profile updated!");
    },
    onError: () => toast.error("Failed to update profile"),
  });

  const toggleItem = (
    item: string,
    current: string[],
    setter: (v: string[]) => void
  ) => {
    setter(
      current.includes(item)
        ? current.filter((i) => i !== item)
        : [...current, item]
    );
  };

  const saveInterests = () => {
    updateMutation.mutate({
      interested_domains: selectedDomains,
      programming_languages: selectedLangs,
      preferred_platforms: selectedPlatforms,
    });
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      toast.error("File size must be under 5MB");
      return;
    }
    try {
      await resumeService.uploadResume(file);
      queryClient.invalidateQueries({ queryKey: ["my-resumes"] });
      toast.success("Resume uploaded and processed!");
    } catch {
      toast.error("Upload failed. Please try again.");
    }
  };

  const handleResumeMatch = async (resumeId: string) => {
    setMatchLoading(true);
    try {
      const results = await resumeService.matchWithEvents(resumeId, 6);
      setResumeMatchResults(results);
      toast.success("Matched your resume with events!");
    } catch {
      toast.error("Resume matching failed");
    } finally {
      setMatchLoading(false);
    }
  };

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <User className="w-7 h-7 text-primary" />
          Profile & Settings
        </h1>
        <p className="text-muted-foreground mt-1">
          Customize your preferences for better recommendations
        </p>
      </div>

      <Tabs defaultValue="interests" className="space-y-6">
        <TabsList className="glass border border-border/50 h-auto p-1 gap-1 flex-wrap">
          <TabsTrigger value="interests" className="data-[state=active]:gradient-primary data-[state=active]:text-white">
            Interests
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:gradient-primary data-[state=active]:text-white">
            Notifications
          </TabsTrigger>
          <TabsTrigger value="resume" className="data-[state=active]:gradient-primary data-[state=active]:text-white">
            Resume
          </TabsTrigger>
          <TabsTrigger value="account" className="data-[state=active]:gradient-primary data-[state=active]:text-white">
            Account
          </TabsTrigger>
        </TabsList>

        {/* Interests tab */}
        <TabsContent value="interests" className="space-y-6">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass rounded-2xl p-6 border border-border/50 space-y-6">
            <h3 className="font-semibold flex items-center gap-2">
              <Globe className="w-5 h-5 text-primary" />
              Interest Domains
            </h3>
            <div className="flex flex-wrap gap-2">
              {DOMAINS.map((d) => (
                <button
                  key={d}
                  onClick={() => toggleItem(d, selectedDomains, setSelectedDomains)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                    selectedDomains.includes(d)
                      ? "gradient-primary text-white border-transparent"
                      : "glass border-border/50 text-muted-foreground hover:text-foreground hover:border-primary/30"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>

            <h3 className="font-semibold flex items-center gap-2">
              <Code2 className="w-5 h-5 text-primary" />
              Programming Languages
            </h3>
            <div className="flex flex-wrap gap-2">
              {LANGUAGES.map((l) => (
                <button
                  key={l}
                  onClick={() => toggleItem(l, selectedLangs, setSelectedLangs)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                    selectedLangs.includes(l)
                      ? "gradient-primary text-white border-transparent"
                      : "glass border-border/50 text-muted-foreground hover:text-foreground hover:border-primary/30"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>

            <h3 className="font-semibold">Preferred Platforms</h3>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS_LIST.map((p) => (
                <button
                  key={p}
                  onClick={() => toggleItem(p, selectedPlatforms, setSelectedPlatforms)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all capitalize ${
                    selectedPlatforms.includes(p)
                      ? "gradient-primary text-white border-transparent"
                      : "glass border-border/50 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            <Button
              onClick={saveInterests}
              disabled={updateMutation.isPending}
              className="gradient-primary text-white border-0"
            >
              {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              Save Interests
            </Button>
          </motion.div>
        </TabsContent>

        {/* Notifications tab */}
        <TabsContent value="notifications">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass rounded-2xl p-6 border border-border/50 space-y-6">
            <h3 className="font-semibold flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary" />
              Notification Settings
            </h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 glass rounded-xl border border-border/30">
                <div>
                  <div className="font-medium">Email Notifications</div>
                  <div className="text-sm text-muted-foreground">Receive daily digests and alerts via email</div>
                </div>
                <Switch
                  checked={profile?.email_notifications ?? true}
                  onCheckedChange={(v) => updateMutation.mutate({ email_notifications: v })}
                />
              </div>

              <div className="flex items-center justify-between p-4 glass rounded-xl border border-border/30">
                <div>
                  <div className="font-medium">Telegram Notifications</div>
                  <div className="text-sm text-muted-foreground">Get instant alerts via Telegram bot</div>
                </div>
                <Switch
                  checked={profile?.telegram_notifications ?? false}
                  onCheckedChange={(v) => updateMutation.mutate({ telegram_notifications: v })}
                />
              </div>

              <div className="p-4 glass rounded-xl border border-border/30 space-y-3">
                <Label>Telegram Chat ID</Label>
                <Input
                  placeholder="Your Telegram chat_id (start a chat with @userinfobot)"
                  defaultValue={profile?.telegram_chat_id || ""}
                  className="bg-secondary/30"
                  onBlur={(e) => updateMutation.mutate({ telegram_chat_id: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  Start a chat with @userinfobot on Telegram to get your Chat ID, then add our bot.
                </p>
              </div>

              <div className="p-4 glass rounded-xl border border-border/30 space-y-3">
                <Label>Notification Frequency</Label>
                <Select
                  defaultValue={profile?.notification_frequency || "daily"}
                  onValueChange={(v: string | null) => updateMutation.mutate({ notification_frequency: (v || "daily") as any })}
                >
                  <SelectTrigger className="bg-secondary/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="instant">Instant (every new event)</SelectItem>
                    <SelectItem value="daily">Daily Digest</SelectItem>
                    <SelectItem value="weekly">Weekly Summary</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </motion.div>
        </TabsContent>

        {/* Resume tab */}
        <TabsContent value="resume" className="space-y-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass rounded-2xl p-6 border border-border/50 space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              Resume Matching
            </h3>
            <p className="text-muted-foreground text-sm">
              Upload your resume and AI will extract your skills and match you with the best opportunities.
            </p>

            <label className="flex flex-col items-center gap-4 p-8 rounded-xl border-2 border-dashed border-border hover:border-primary/50 transition-all cursor-pointer">
              <Upload className="w-10 h-10 text-muted-foreground" />
              <div className="text-center">
                <div className="font-medium">Upload Resume (PDF)</div>
                <div className="text-sm text-muted-foreground">Max 5MB</div>
              </div>
              <input type="file" accept=".pdf" className="hidden" onChange={handleResumeUpload} />
            </label>

            {resumes.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-medium text-sm text-muted-foreground">Your Resumes</h4>
                {resumes.map((resume) => (
                  <div key={resume.id} className="flex items-center gap-3 p-3 glass rounded-xl border border-border/30">
                    <FileText className="w-5 h-5 text-primary shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{resume.filename}</div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(resume.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleResumeMatch(resume.id)}
                      disabled={matchLoading}
                      className="text-xs"
                    >
                      {matchLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3 mr-1" />}
                      Match
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {resumeMatchResults.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-semibold flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                Resume Matches
              </h3>
              {resumeMatchResults.map((result, i) => (
                <motion.div
                  key={result.event_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="glass rounded-xl p-4 border border-border/50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium">{result.event_title}</div>
                    <Badge className={`${result.match_percentage >= 80 ? "bg-green-500/20 text-green-400" : result.match_percentage >= 60 ? "bg-yellow-500/20 text-yellow-400" : "bg-orange-500/20 text-orange-400"}`}>
                      {result.match_percentage}% match
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {result.matching_skills?.map((s: string) => (
                      <span key={s} className="px-2 py-0.5 rounded-md bg-primary/20 text-primary text-xs">{s}</span>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground">{result.explanation}</p>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Account tab */}
        <TabsContent value="account">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass rounded-2xl p-6 border border-border/50 space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <User className="w-5 h-5 text-primary" />
              Account Details
            </h3>
            {user && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 glass rounded-xl border border-border/30">
                    <div className="text-xs text-muted-foreground mb-1">Full Name</div>
                    <div className="font-medium">{user.full_name}</div>
                  </div>
                  <div className="p-3 glass rounded-xl border border-border/30">
                    <div className="text-xs text-muted-foreground mb-1">Username</div>
                    <div className="font-medium">@{user.username}</div>
                  </div>
                  <div className="p-3 glass rounded-xl border border-border/30">
                    <div className="text-xs text-muted-foreground mb-1">Email</div>
                    <div className="font-medium">{user.email}</div>
                  </div>
                  <div className="p-3 glass rounded-xl border border-border/30">
                    <div className="text-xs text-muted-foreground mb-1">Status</div>
                    <div className="font-medium flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${user.is_active ? "bg-green-400" : "bg-red-400"}`} />
                      {user.is_active ? "Active" : "Inactive"}
                    </div>
                  </div>
                </div>
                <div className="p-3 glass rounded-xl border border-border/30">
                  <div className="text-xs text-muted-foreground mb-1">Member Since</div>
                  <div className="font-medium">{new Date(user.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</div>
                </div>
              </div>
            )}
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
