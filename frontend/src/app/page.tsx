"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Rocket, Zap, Target, Bell, Search, Users, ArrowRight,
  Star, Shield, Globe, Code2, Brain, Trophy
} from "lucide-react";
import { Button } from "@/components/ui/button";

const FEATURES = [
  { icon: Search, title: "AI-Powered Search", desc: "Find opportunities with natural language. Ask anything." },
  { icon: Bell, title: "Smart Notifications", desc: "Get notified via email & Telegram the moment new events drop." },
  { icon: Brain, title: "Resume Matching", desc: "Upload your resume. See which events match your skills." },
  { icon: Target, title: "Personalized Feed", desc: "AI learns your interests and ranks events just for you." },
  { icon: Globe, title: "15+ Platforms", desc: "Unstop, Devfolio, Kaggle, GSoC, HackerEarth and more." },
  { icon: Trophy, title: "Ranked Results", desc: "Every event is scored 0–100 by our AI for quality." },
];

const PLATFORMS = [
  "Unstop", "Devfolio", "HackerEarth", "Kaggle", "Devpost",
  "Codeforces", "GSoC", "MLH", "Microsoft", "Google",
];

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
            AI Opportunity Scout automatically finds hackathons, internships, coding contests, 
            and developer events from 15+ platforms — ranked and summarized just for you.
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
        <p>© 2025 AI Opportunity Scout. Built to help students win.</p>
      </footer>
    </div>
  );
}
