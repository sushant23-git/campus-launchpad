"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  CheckSquare,
  Award,
  Users,
  FolderKanban,
  Trophy,
  Shield,
  LogOut,
  Flame,
  User as UserIcon,
  RefreshCw
} from "lucide-react";
import api from "@/lib/api";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      const res = await api.get("/auth/me");
      if (res.data.success) {
        setProfile(res.data.data);
      }
    } catch (err) {
      // Unauthenticated
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [pathname]);

  const handleSyncGithub = async () => {
    try {
      await api.post("/github/sync");
      fetchProfile();
    } catch (err) {
      console.error("Failed to sync GitHub", err);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    router.push("/login");
  };

  if (loading) {
    return (
      <aside className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col items-center justify-center min-h-screen">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
      </aside>
    );
  }

  if (!profile) return null;

  const links = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Curriculum", href: "/curriculum", icon: BookOpen },
    { name: "Assessments", href: "/quizzes", icon: Award },
    { name: "Peer Group", href: "/peers", icon: Users },
    { name: "Project Teams", href: "/projects", icon: FolderKanban },
    { name: "Leaderboard", href: "/leaderboard", icon: Trophy },
  ];

  const isAdminOrMentor = profile.role === "admin" || profile.role === "mentor";

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between min-h-screen sticky top-0">
      <div className="p-6">
        {/* Brand */}
        <div className="flex items-center gap-2 mb-8">
          <div className="bg-blue-600 p-2 rounded-lg text-white font-bold text-lg">CL</div>
          <span className="font-extrabold text-lg tracking-wider text-slate-100">Campus Launchpad</span>
        </div>

        {/* User Info Capsule */}
        <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400">
              <UserIcon className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-200 truncate max-w-[140px]">
                {profile.profile?.full_name || "New Student"}
              </h4>
              <p className="text-xs text-slate-400 capitalize">{profile.role}</p>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-900 flex justify-between items-center text-xs">
            <span className="text-slate-400">Lvl {profile.profile?.level || 1}</span>
            <span className="font-semibold text-blue-400">{profile.profile?.xp || 0} XP</span>
            <div className="flex items-center gap-1 text-orange-500 font-bold">
              <Flame className="w-4 h-4 fill-orange-500 animate-pulse" />
              <span>{profile.profile?.current_streak || 0}d</span>
            </div>
          </div>
          {profile.profile?.github_username && (
            <button
              onClick={handleSyncGithub}
              className="mt-3 w-full bg-slate-900 hover:bg-slate-850 text-slate-300 py-1 rounded text-2xs transition flex items-center justify-center gap-1"
            >
              <RefreshCw className="w-3 h-3" /> Sync Git Activity
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const active = pathname.startsWith(link.href);
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200 ${
                  active
                    ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`}
              >
                <Icon className="w-5 h-5" />
                {link.name}
              </Link>
            );
          })}

          {isAdminOrMentor && (
            <Link
              href="/admin"
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200 mt-4 ${
                pathname.startsWith("/admin")
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-900/30"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              }`}
            >
              <Shield className="w-5 h-5" />
              Admin Console
            </Link>
          )}
        </nav>
      </div>

      {/* Footer / Logout */}
      <div className="p-6 border-t border-slate-800">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-4 py-3 text-slate-400 hover:bg-red-500/10 hover:text-red-400 rounded-lg text-sm font-semibold transition-colors duration-250"
        >
          <LogOut className="w-5 h-5" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
