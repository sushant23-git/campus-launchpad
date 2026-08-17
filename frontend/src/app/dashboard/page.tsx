"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import api from "../../lib/api";
import {
  Flame, Award, BookOpen, AlertCircle, Sparkles, CheckCircle, Github, Bell, ArrowUpRight
} from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [profile, setProfile] = useState<any>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [insight, setInsight] = useState<any>(null);
  const [githubUser, setGithubUser] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      // 1. Me Profile
      const meRes = await api.get("/auth/me");
      if (meRes.data.success) {
        setProfile(meRes.data.data);
      }

      // 2. Weekly progress metrics
      const metricsRes = await api.get("/metrics/progress");
      if (metricsRes.data.success) {
        setMetrics(metricsRes.data.data);
      }

      // 3. Notifications
      const notesRes = await api.get("/notifications");
      if (notesRes.data.success) {
        setNotifications(notesRes.data.data.slice(0, 5)); // show top 5
      }

      // 4. AI Insights for week 1
      const aiRes = await api.get("/ai/insights?week_number=1");
      if (aiRes.data.success) {
        setInsight(aiRes.data.data);
      }
    } catch (err) {
      console.error("Error fetching dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleMarkNotificationRead = async (id: string) => {
    try {
      await api.post(`/notifications/${id}/read`);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const handleConnectGithub = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post("/github/connect", { github_username: githubUser });
      if (res.data.success) {
        fetchDashboardData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading student workspace...
      </div>
    );
  }

  const latestMetrics = metrics[metrics.length - 1] || {
    overall_progress: 0.0,
    task_score: 0.0,
    assessment_score: 0.0,
    peer_score: 0.0,
    consistency_score: 0.0
  };

  // Determine Level progress
  const currentXP = profile?.profile?.xp || 0;
  const level = profile?.profile?.level || 1;
  const xpThresholds = [0, 100, 250, 500, 1000, 2000];
  const minXP = xpThresholds[level - 1] || 0;
  const maxXP = xpThresholds[level] || 2500;
  const levelProgressPercent = Math.min(100, ((currentXP - minXP) / (maxXP - minXP)) * 100);

  return (
    <div className="flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-grow p-8 max-w-6xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-100">Welcome Back, {profile?.profile?.full_name}!</h1>
            <p className="text-slate-400 text-sm mt-1">Here is a summary of your weekly progress and alerts.</p>
          </div>
          <div className="flex gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-center">
              <span className="text-slate-400 text-2xs uppercase font-bold tracking-wider block">XP SCORE</span>
              <span className="text-xl font-black text-blue-400">{profile?.profile?.xp || 0} XP</span>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-center flex items-center gap-2">
              <Flame className="w-6 h-6 text-orange-500 fill-orange-500 animate-pulse" />
              <div className="text-left">
                <span className="text-slate-400 text-2xs uppercase font-bold tracking-wider block">STREAK</span>
                <span className="text-xl font-black text-slate-100">{profile?.profile?.current_streak || 0} Days</span>
              </div>
            </div>
          </div>
        </div>

        {/* Level details & progress bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
          <div className="flex justify-between items-center mb-2 text-sm font-bold">
            <span className="text-slate-300">Level {level}: Explorer</span>
            <span className="text-slate-400">{currentXP} / {maxXP} XP</span>
          </div>
          <div className="w-full bg-slate-950 rounded-full h-3.5 border border-slate-850 overflow-hidden">
            <div
              className="bg-blue-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${levelProgressPercent}%` }}
            />
          </div>
        </div>

        {/* Grid: Metrics, Notifications, AI Insights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Column 1: Weekly Progress Metrics */}
          <div className="md:col-span-2 space-y-8">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="font-extrabold text-lg text-slate-200 mb-6 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-blue-500" />
                Current Week Progress
              </h3>

              <div className="grid grid-cols-2 gap-6">
                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl">
                  <span className="text-xs text-slate-400 font-bold block mb-1">Overall Completion</span>
                  <span className="text-2xl font-black text-slate-100">{latestMetrics.overall_progress.toFixed(1)}%</span>
                </div>
                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl">
                  <span className="text-xs text-slate-400 font-bold block mb-1">Assignments Done</span>
                  <span className="text-2xl font-black text-blue-400">{latestMetrics.task_score.toFixed(1)}%</span>
                </div>
                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl">
                  <span className="text-xs text-slate-400 font-bold block mb-1">Quiz Scores Avg</span>
                  <span className="text-2xl font-black text-indigo-400">{latestMetrics.assessment_score.toFixed(1)}%</span>
                </div>
                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl">
                  <span className="text-xs text-slate-400 font-bold block mb-1">Consistency (Active Days)</span>
                  <span className="text-2xl font-black text-emerald-400">{latestMetrics.consistency_score.toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* AI Insights Grounded Box */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-blue-600/10 text-blue-400 font-bold text-3xs uppercase tracking-widest px-3 py-1.5 rounded-bl-xl border-l border-b border-slate-800 flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> Grounded AI
              </div>
              <h3 className="font-extrabold text-lg text-slate-200 mb-4">Personal Coach Recommendations</h3>
              
              {insight ? (
                <div className="space-y-4">
                  <div>
                    <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Summary</h5>
                    <p className="text-sm text-slate-355 mt-1 leading-relaxed">{insight.summary}</p>
                  </div>
                  <div className="pt-3 border-t border-slate-850">
                    <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Action Items</h5>
                    <p className="text-sm text-blue-400 mt-1 font-semibold leading-relaxed">{insight.recommendation}</p>
                  </div>
                </div>
              ) : (
                <p className="text-slate-400 text-sm">Generating performance insights...</p>
              )}
            </div>
          </div>

          {/* Column 2: Notifications & Integrations */}
          <div className="space-y-8">
            
            {/* Notification center */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="font-extrabold text-lg text-slate-200 mb-4 flex items-center gap-2">
                <Bell className="w-5 h-5 text-blue-500" />
                Alerts & Updates
              </h3>
              
              <div className="space-y-3">
                {notifications.length > 0 ? (
                  notifications.map(n => (
                    <div key={n.id} className="bg-slate-950 border border-slate-850 p-3 rounded-xl flex justify-between items-start">
                      <div>
                        <h5 className="font-bold text-xs text-slate-300">{n.title}</h5>
                        <p className="text-2xs text-slate-400 mt-0.5 leading-relaxed">{n.message}</p>
                      </div>
                      <button
                        onClick={() => handleMarkNotificationRead(n.id)}
                        className="text-slate-500 hover:text-slate-355 text-2xs p-1"
                      >
                        Dismiss
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 text-xs text-center py-4">No active warnings or alerts.</p>
                )}
              </div>
            </div>

            {/* GitHub integration block */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="font-extrabold text-lg text-slate-200 mb-4 flex items-center gap-2">
                <Github className="w-5 h-5 text-indigo-500" />
                Git Sync & Contributions
              </h3>
              
              {profile?.profile?.github_username ? (
                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl text-center">
                  <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <h5 className="font-bold text-slate-300">Connected: @{profile.profile.github_username}</h5>
                  <p className="text-2xs text-slate-500 mt-1">Platform automatically tracks repository commits and pull requests.</p>
                </div>
              ) : (
                <form onSubmit={handleConnectGithub} className="space-y-3">
                  <p className="text-2xs text-slate-400 leading-relaxed">
                    Connect your GitHub username to automatically check-in streaks via code commits.
                  </p>
                  <input
                    type="text"
                    placeholder="github_username"
                    value={githubUser}
                    onChange={(e) => setGithubUser(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3.5 text-xs"
                    required
                  />
                  <button
                    type="submit"
                    className="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-2 rounded-xl text-xs transition"
                  >
                    Connect GitHub Profile
                  </button>
                </form>
              )}
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}
