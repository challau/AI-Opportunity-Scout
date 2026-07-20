"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Rocket, Zap, Target, Bell, Search, Users, ArrowRight,
  Star, Shield, Globe, Code2, Brain, Trophy, UserPlus,
  Settings2, Mail, ChevronDown, Database, Layers, Filter, BarChart3
} from "lucide-react";
import { Button } from "@/components/ui/button";

const FEATURES = [
  { icon: Search, title: "AI-Powered Search", desc: "Find opportunities with natural language. Ask anything." },
  { icon: Bell, title: "Smart Notifications", desc: "Get an email digest every 6 hours with only new opportunities." },
  { icon: Brain, title: "Resume Matching", desc: "Upload your resume. See which events match your skills." },
  { icon: Target, title: "Personalized Feed", desc: "AI learns your interests and ranks events just for you." },
  { icon: Globe, title: "9+ Platforms", desc: "Unstop, Devfolio, Codeforces, LeetCode, AtCoder and more." },
  { icon: Trophy, title: "Ranked Results", desc: "Every event is scored 0–100 by our AI for quality." },
];

const PLATFORMS = [
  "Unstop", "Devfolio", "HackerEarth", "Hack2Skill", "Devpost",
  "Codeforces", "CodeChef", "LeetCode", "AtCoder",
];

const HOW_IT_WORKS = [
  { icon: UserPlus, title: "1. Create your account", desc: "Sign up free in under a minute — just email and password." },
  { icon: Settings2, title: "2. Pick your platforms", desc: "Choose any mix of hackathon and coding-contest sources." },
  { icon: Mail, title: "3. Get personalized alerts", desc: "Every 6 hours we email you only the NEW events matching your picks — straight to your own inbox." },
];

const PIPELINE_STEPS = [
  { icon: Globe, label: "Crawl", desc: "9+ platforms scanned automatically" },
  { icon: Layers, label: "Normalize", desc: "Unified into one clean schema" },
  { icon: Filter, label: "Deduplicate", desc: "Content hashing removes repeats" },
  { icon: BarChart3, label: "Rank", desc: "AI scores every event 0–100" },
  { icon: Database, label: "Store", desc: "Saved with semantic embeddings" },
  { icon: Bell, label: "Notify", desc: "Personalized email digests" },
];

const TECH_STACK = [
  "Next.js", "React", "TypeScript", "Tailwind CSS",
  "FastAPI", "Python", "PostgreSQL", "pgvector",
  "Redis", "Vercel", "Railway", "Neon",
];

const FAQS = [
  {
    q: "Is AI Opportunity Scout free?",
    a: "Yes — creating an account, browsing opportunities, and receiving email digests are completely free.",
  },
  {
    q: "How often will I get emails?",
    a: "Every 6 hours, and only when there are NEW opportunities matching the platforms you selected. No new events, no email — never spam.",
  },
  {
    q: "Which platforms are monitored?",
    a: "Hackathons: Unstop, Devfolio, HackerEarth, Hack2Skill, Devpost. Coding contests: Codeforces, CodeChef, LeetCode, AtCoder. More are on the roadmap.",
  },
  {
    q: "Can I choose which platforms I hear about?",
    a: "Absolutely. Your profile lets you toggle each platform individually — your digest only ever includes events from the sources you picked.",
  },
  {
    q: "How do I stop notifications?",
    a: "Turn off the email toggle in Profile → Notifications at any time, or use the unsubscribe link in any digest.",
  },
];

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <button
      onClick={() => setOpen(!open)}
      className="w-full text-left glass rounded-xl border border-border/50 p-5 hover:border-primary/30 transition-all"
    >
      <div className="flex items-center justify-between gap-4">
        <span className="font-medium">{q}</span>
        <ChevronDown className={`w-4 h-4 shrink-0 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
      </div>
      {open && <p className="mt-3 text-sm text-muted-foreground leading-relaxed">{a}</p>}
    </button>
  );
}

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) router.push("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4 glass border-b border-border/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
            <Rocket className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg gradient-text">AI Opportunity Scout</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Sign in</Button>
          </Link>
          <Link href="/register">
            <Button size="sm" className="gradient-primary text-white border-0">
              Get Started Free
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 pt-24 pb-20 px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-primary/20 text-sm text-primary mb-8">
            <Zap className="w-4 h-4" />
            <span>AI-powered opportunity discovery</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 leading-tight">
            Never Miss a{" "}
            <span className="gradient-text">Hackathon</span>
            <br />
            Again
          </h1>

          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
            Never miss a hackathon, coding contest, or developer opportunity again.
            AI Opportunity Scout monitors 9+ platforms around the clock, ranks every
            event with AI, and emails you a personalized digest — so the next big
            opportunity finds you.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register">
              <Button size="lg" className="gradient-primary text-white border-0 px-8 py-6 text-lg font-semibold glow-hover">
                Start Discovering Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="px-8 py-6 text-lg">
                Sign In
              </Button>
            </Link>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="flex flex-wrap justify-center gap-8 mt-16"
        >
          {[
            { value: "15+", label: "Platforms Monitored" },
            { value: "1000+", label: "Events Tracked" },
            { value: "AI", label: "Powered Rankings" },
            { value: "Free", label: "To Get Started" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold gradient-text">{stat.value}</div>
              <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Platform logos */}
      <section className="relative z-10 py-12 px-6 overflow-hidden">
        <p className="text-center text-muted-foreground text-sm mb-6 uppercase tracking-widest">
          Monitoring opportunities from
        </p>
        <div className="flex flex-wrap justify-center gap-3 max-w-3xl mx-auto">
          {PLATFORMS.map((p) => (
            <span
              key={p}
              className="px-4 py-2 glass rounded-full text-sm text-muted-foreground border border-border/50 hover:border-primary/30 hover:text-foreground transition-all"
            >
              {p}
            </span>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">
              Everything You Need to{" "}
              <span className="gradient-text">Win</span>
            </h2>
            <p className="text-muted-foreground text-lg">
              A complete platform built for ambitious student developers
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass rounded-2xl p-6 border border-border/50 hover:border-primary/30 transition-all glow-hover group"
              >
                <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="relative z-10 py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-14">
            <h2 className="text-4xl font-bold mb-4">How It <span className="gradient-text">Works</span></h2>
            <p className="text-muted-foreground text-lg">Three steps between you and your next opportunity</p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {HOW_IT_WORKS.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="glass rounded-2xl p-8 border border-border/50 text-center hover:border-primary/30 transition-all"
              >
                <div className="w-14 h-14 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-5">
                  <step.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{step.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Pipeline */}
      <section className="relative z-10 py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-14">
            <h2 className="text-4xl font-bold mb-4">The <span className="gradient-text">AI Pipeline</span></h2>
            <p className="text-muted-foreground text-lg">What happens between a platform posting an event and it landing in your inbox</p>
          </motion.div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {PIPELINE_STEPS.map((step, i) => (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass rounded-xl p-5 border border-border/50 text-center hover:border-primary/30 transition-all"
              >
                <step.icon className="w-6 h-6 text-primary mx-auto mb-3" />
                <div className="font-semibold text-sm mb-1">{step.label}</div>
                <div className="text-xs text-muted-foreground leading-snug">{step.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Email alerts */}
      <section className="relative z-10 py-20 px-6">
        <div className="max-w-4xl mx-auto glass rounded-3xl border border-border/50 p-10 md:p-12">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center shrink-0">
              <Mail className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-3xl font-bold mb-3">Email Alerts That <span className="gradient-text">Respect Your Inbox</span></h2>
              <p className="text-muted-foreground leading-relaxed">
                Every 6 hours, our scheduler checks all your selected platforms. If — and only if — new
                opportunities appeared, you get one clean digest with the event name, platform, deadline,
                prize, eligibility, and a direct registration link. Duplicates are removed automatically,
                and every user receives their own personalized email. Unsubscribe anytime with one click.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Tech stack */}
      <section className="relative z-10 py-16 px-6">
        <p className="text-center text-muted-foreground text-sm mb-6 uppercase tracking-widest">
          Built with a modern production stack
        </p>
        <div className="flex flex-wrap justify-center gap-3 max-w-3xl mx-auto">
          {TECH_STACK.map((t) => (
            <span key={t} className="px-4 py-2 glass rounded-full text-sm text-muted-foreground border border-border/50 hover:border-primary/30 hover:text-foreground transition-all">
              {t}
            </span>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="relative z-10 py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Frequently Asked <span className="gradient-text">Questions</span></h2>
          </motion.div>
          <div className="space-y-3">
            {FAQS.map((f) => (
              <FaqItem key={f.q} q={f.q} a={f.a} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-20 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-3xl mx-auto glass rounded-3xl p-12 text-center border border-primary/20 glow-primary"
        >
          <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-6 animate-float">
            <Rocket className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-4xl font-bold mb-4">
            Ready to Scout Your Next{" "}
            <span className="gradient-text">Opportunity?</span>
          </h2>
          <p className="text-muted-foreground mb-8 text-lg">
            Join thousands of students who never miss a hackathon or internship.
          </p>
          <Link href="/register">
            <Button size="lg" className="gradient-primary text-white border-0 px-10 py-6 text-lg font-bold glow-hover">
              Get Started — It&apos;s Free
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-8 px-6 border-t border-border/50 text-center text-muted-foreground text-sm">
        <p>© 2026 AI Opportunity Scout. Built to help students win.</p>
      </footer>
    </div>
  );
}
