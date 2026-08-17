"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import api from "@/lib/api";
import {
  Trophy, ArrowUp, ArrowDown, Minus, Flame, Award, HelpCircle
} from "lucide-react";

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [week, setWeek] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/metrics/leaderboard?week_number=${week}`);
      if (res.data.success) {
        setLeaderboard(res.data.data);
      }
    } catch (err) {
      console.error("Leaderboard fetch error", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, [week]);

  return (
    <div className="flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-grow p-8 max-w-6xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-100 flex items-center gap-2">
              <Trophy className="w-8 h-8 text-amber-500 fill-amber-500/10 animate-bounce" />
              Cohort Leaderboard
            </h1>
            <p className="text-slate-400 text-sm mt-1">Weekly rank updates based on objective performance scores.</p>
          </div>

          {/* Week Selector */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1.5 rounded-xl">
            {[1, 2, 3, 4, 5, 6].map((w) => (
              <button
                key={w}
                onClick={() => setWeek(w)}
                className={`py-1.5 px-3.5 rounded-lg font-bold text-xs transition ${
                  week === w
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Week {w}
              </button>
            ))}
          </div>
        </div>

        {/* Standings Table card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="text-center py-20 text-slate-500 text-sm">
              Loading weekly standings standings...
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950 border-b border-slate-800 text-2xs font-extrabold text-slate-400 uppercase tracking-wider">
                  <th className="py-4 px-6 text-center w-20">Rank</th>
                  <th className="py-4 px-6">Teammate Name</th>
                  <th className="py-4 px-6 text-center">Level Badge</th>
                  <th className="py-4 px-6 text-center">Active Streak</th>
                  <th className="py-4 px-6 text-center">XP Points</th>
                  <th className="py-4 px-6 text-center">Overall Progress</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {leaderboard.length > 0 ? (
                  leaderboard.map((student, idx) => {
                    const movement = student.rank_movement || 0;
                    
                    return (
                      <tr key={student.student_id} className="hover:bg-slate-900/50 transition">
                        {/* Rank & Movement */}
                        <td className="py-4.5 px-6 text-center font-black text-slate-100 flex items-center justify-center gap-2">
                          <span className="text-sm">{student.rank}</span>
                          
                          {/* Rank shift indicator */}
                          {movement > 0 ? (
                            <span className="flex items-center text-3xs font-extrabold text-emerald-500">
                              <ArrowUp className="w-3.5 h-3.5 stroke-[3px]" /> {movement}
                            </span>
                          ) : movement < 0 ? (
                            <span className="flex items-center text-3xs font-extrabold text-red-500">
                              <ArrowDown className="w-3.5 h-3.5 stroke-[3px]" /> {Math.abs(movement)}
                            </span>
                          ) : (
                            <span className="text-slate-600">
                              <Minus className="w-3.5 h-3.5 stroke-[3px]" />
                            </span>
                          )}
                        </td>

                        {/* Name */}
                        <td className="py-4.5 px-6 font-bold text-sm text-slate-200">
                          {student.full_name}
                        </td>

                        {/* Level badge */}
                        <td className="py-4.5 px-6 text-center">
                          <span className="inline-flex items-center gap-1 bg-blue-600/10 border border-blue-500/20 text-blue-400 font-extrabold text-3xs px-2.5 py-1 rounded-full uppercase">
                            <Award className="w-3.5 h-3.5" /> Lvl {student.level}
                          </span>
                        </td>

                        {/* Streak */}
                        <td className="py-4.5 px-6 text-center">
                          <div className="inline-flex items-center gap-1 font-extrabold text-orange-500 text-xs">
                            <Flame className="w-4 h-4 fill-orange-500" />
                            <span>{student.streak}d</span>
                          </div>
                        </td>

                        {/* XP */}
                        <td className="py-4.5 px-6 text-center text-sm font-extrabold text-slate-100">
                          {student.xp}
                        </td>

                        {/* Overall Progress */}
                        <td className="py-4.5 px-6 text-center">
                          <span className="font-extrabold text-sm text-blue-400">
                            {student.overall_progress.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-slate-500 text-sm">
                      Standings for Week {week} have not been frozen yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
