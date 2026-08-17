"use client";

import React, { useEffect, useState, useRef } from "react";
import Sidebar from "../../components/Sidebar";
import api from "../../lib/api";
import {
  Lock, Unlock, CheckCircle, Play, ChevronRight, FileText, Clock, AlertCircle, RefreshCw
} from "lucide-react";

export default function CurriculumPage() {
  const [weeks, setWeeks] = useState<any[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<any>(null);
  const [modules, setModules] = useState<any[]>([]);
  const [activeModule, setActiveModule] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Heartbeat tracking refs
  const heartbeatTimer = useRef<NodeJS.Timeout | null>(null);
  const activeModuleRef = useRef<any>(null);

  const fetchWeeks = async () => {
    try {
      const res = await api.get("/curriculum/weeks");
      if (res.data.success) {
        setWeeks(res.data.data);
        if (res.data.data.length > 0 && !selectedWeek) {
          // Select first unlocked week by default
          const firstUnlocked = res.data.data.find((w: any) => !w.is_locked) || res.data.data[0];
          setSelectedWeek(firstUnlocked);
          fetchModules(firstUnlocked.id);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchModules = async (weekId: string) => {
    try {
      const res = await api.get(`/curriculum/modules?week_id=${weekId}`);
      if (res.data.success) {
        setModules(res.data.data);
        setActiveModule(null); // Clear active reader
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchWeeks();
  }, []);

  // Update active module reference for timer callback access
  useEffect(() => {
    activeModuleRef.current = activeModule;
    
    // Manage timers
    if (activeModule) {
      // Clear old
      if (heartbeatTimer.current) clearInterval(heartbeatTimer.current);
      
      // Start 15s interval tick
      heartbeatTimer.current = setInterval(async () => {
        if (!activeModuleRef.current) return;
        try {
          const res = await api.post(`/curriculum/modules/${activeModuleRef.current.id}/heartbeat`, {
            duration_seconds: 15
          });
          if (res.data.success) {
            const { is_completed, current_duration } = res.data.data;
            if (is_completed) {
              // Update module list checklist checkmark
              setModules(prev => prev.map(m => m.id === activeModuleRef.current.id ? { ...m, is_completed: true } : m));
            }
          }
        } catch (err) {
          console.error("Heartbeat sync failed", err);
        }
      }, 15000);
    } else {
      if (heartbeatTimer.current) {
        clearInterval(heartbeatTimer.current);
        heartbeatTimer.current = null;
      }
    }

    return () => {
      if (heartbeatTimer.current) clearInterval(heartbeatTimer.current);
    };
  }, [activeModule]);

  const handleSelectWeek = (week: any) => {
    if (week.is_locked) return;
    setSelectedWeek(week);
    fetchModules(week.id);
  };

  const handleStartReading = (mod: any) => {
    setActiveModule(mod);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading syllabus roadmaps...
      </div>
    );
  }

  return (
    <div className="flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-grow p-8 max-w-6xl grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Column 1: Week nodes roadmap list */}
        <div className="space-y-6">
          <h1 className="text-3xl font-extrabold text-slate-100 mb-6">Curriculum Roadmap</h1>
          
          <div className="relative border-l-2 border-slate-800 ml-4 space-y-8 py-2">
            {weeks.map((week) => {
              const active = selectedWeek?.id === week.id;
              const isLocked = week.is_locked;
              
              return (
                <div key={week.id} className="relative pl-6">
                  {/* Icon indicator */}
                  <div className={`absolute -left-[13px] top-1.5 w-6 h-6 rounded-full border-2 flex items-center justify-center transition ${
                    isLocked 
                      ? "bg-slate-950 border-slate-800 text-slate-500" 
                      : (active ? "bg-blue-600 border-blue-600 text-white animate-pulse" : "bg-slate-900 border-slate-700 text-slate-355")
                  }`}>
                    {isLocked ? <Lock className="w-3.5 h-3.5" /> : (active ? <Play className="w-3.5 h-3.5 fill-current" /> : <Unlock className="w-3.5 h-3.5" />)}
                  </div>

                  {/* Node Content */}
                  <div
                    onClick={() => handleSelectWeek(week)}
                    className={`cursor-pointer border p-4 rounded-xl transition ${
                      isLocked 
                        ? "bg-slate-900/30 border-slate-900/50 text-slate-550" 
                        : (active ? "bg-slate-900 border-blue-600/50 text-slate-100" : "bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-200")
                    }`}
                  >
                    <span className="text-2xs font-extrabold text-blue-500 block mb-1">WEEK {week.week_number}</span>
                    <h3 className="font-bold text-sm leading-snug">{week.title}</h3>
                    
                    {isLocked && week.lock_reason && (
                      <span className="text-3xs text-red-400 block mt-2 font-semibold">
                        🔒 Locked: {week.lock_reason}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Column 2 & 3: Modules detail reader panels */}
        <div className="md:col-span-2 space-y-6">
          {selectedWeek && (
            <div>
              <span className="text-xs text-blue-500 font-extrabold block">WEEK {selectedWeek.week_number} SYLLABUS</span>
              <h2 className="text-2xl font-black text-slate-100">{selectedWeek.title}</h2>
              <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                Complete modules reading to unlock follow-up coding tasks and quizzes.
              </p>
            </div>
          )}

          {activeModule ? (
            /* Active Reader panel */
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 animate-fade-in">
              <div className="flex justify-between items-center pb-4 border-b border-slate-800">
                <div>
                  <span className="text-3xs font-extrabold text-blue-500 block">ACTIVE LESSON</span>
                  <h3 className="font-bold text-lg text-slate-100">{activeModule.title}</h3>
                </div>
                <button
                  onClick={() => setActiveModule(null)}
                  className="bg-slate-850 hover:bg-slate-800 text-slate-300 py-1.5 px-3 rounded-lg text-xs transition"
                >
                  Exit Reader
                </button>
              </div>

              {/* Heartbeat notification badge */}
              <div className="bg-blue-600/10 border border-blue-500/20 text-blue-400 text-2xs p-3 rounded-xl flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-500 animate-spin" />
                <span>Timer active: Platform is tracking reading duration to grant XP.</span>
              </div>

              {/* Module Text Content */}
              <article className="prose prose-invert max-w-none text-slate-355 text-sm leading-relaxed space-y-4 font-mono">
                {activeModule.content_text.split("\n\n").map((para: string, idx: number) => (
                  <p key={idx}>{para}</p>
                ))}
              </article>
            </div>
          ) : (
            /* Module Lists */
            <div className="space-y-4">
              {modules.length > 0 ? (
                modules.map((mod) => (
                  <div
                    key={mod.id}
                    className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex justify-between items-center hover:border-slate-700 transition"
                  >
                    <div className="flex items-start gap-4">
                      <div className="bg-blue-500/10 p-2.5 rounded-lg text-blue-400 mt-0.5">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="font-bold text-sm text-slate-200">{mod.title}</h4>
                        <div className="flex items-center gap-3 text-3xs text-slate-500 font-semibold mt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" />
                            {mod.estimated_reading_minutes} Min Read
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {mod.is_completed ? (
                        <span className="flex items-center gap-1 text-2xs font-extrabold text-emerald-500">
                          <CheckCircle className="w-4 h-4 text-emerald-500" /> COMPLETED
                        </span>
                      ) : (
                        <button
                          onClick={() => handleStartReading(mod)}
                          className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded-lg text-xs transition"
                        >
                          Start Lesson
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 text-sm">No modules populated for this week.</p>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
