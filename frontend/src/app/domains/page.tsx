"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import api from "../../lib/api";
import { Grid, BookOpen, Compass, ChevronRight, CheckCircle2, ShieldAlert, Cpu, Database, Globe } from "lucide-react";

interface TechnicalDomain {
  id: string;
  name: string;
  description: string;
  beginner_learning_activity: string;
  intermediate_learning_activity: string;
  advanced_learning_activity: string;
  exploration_depth?: number; // mock exploration depth
}

export default function DomainHubPage() {
  const [domains, setDomains] = useState<TechnicalDomain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDomains = async () => {
    try {
      const res = await api.get("/projects/domains");
      if (res.data.success) {
        // Map domains with mock exploration progress
        const domainsWithProgress = res.data.data.map((d: any, index: number) => ({
          ...d,
          exploration_depth: index === 0 ? 80 : index === 1 ? 40 : 15,
        }));
        setDomains(domainsWithProgress);
      }
    } catch (err) {
      console.error("Failed to fetch domains", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDomains();
  }, []);

  const handleSelectDomain = (id: string) => {
    setSelectedDomain(id);
  };

  const getDomainIcon = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes("software") || lower.includes("web")) return Globe;
    if (lower.includes("ai") || lower.includes("intelligence") || lower.includes("data")) return Database;
    if (lower.includes("cloud") || lower.includes("devops")) return Cpu;
    return Compass;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading NOXUS Domain Hub...
      </div>
    );
  }

  return (
    <div className="flex bg-slate-950 min-h-screen text-slate-100">
      <Sidebar />

      <main className="flex-grow p-8 max-w-6xl">
        <header className="mb-8">
          <h1 className="text-3xl font-extrabold tracking-tight">Explore Tracks</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Discover engineering tracks, calibrate your learning paths, and audit cohort specialties.
          </p>
        </header>

        {/* Curator Gallery Grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {domains.map((domain) => {
            const Icon = getDomainIcon(domain.name);
            const isSelected = selectedDomain === domain.id;
            const progress = domain.exploration_depth || 0;

            return (
              <div
                key={domain.id}
                onClick={() => handleSelectDomain(domain.id)}
                className={`bg-slate-900 border ${
                  isSelected ? "border-blue-600 shadow-blue-900/10 shadow-lg" : "border-slate-800"
                } rounded-xl p-6 transition-all duration-300 cursor-pointer hover:border-slate-700 hover:shadow-xl flex flex-col justify-between`}
              >
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-slate-955 rounded-lg border border-slate-800 text-blue-400">
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-2xs font-bold bg-blue-600/10 text-blue-400 px-2 py-1 rounded">
                      EXPLORE
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-slate-200 mb-2">{domain.name}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed mb-6">
                    {domain.description}
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Progress Tracker */}
                  <div>
                    <div className="flex justify-between text-2xs font-bold text-slate-400 uppercase mb-1">
                      <span>Exploration Depth</span>
                      <span>{progress}%</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 border border-slate-850 overflow-hidden">
                      <div
                        className="bg-blue-600 h-full rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-xs font-bold text-blue-400 pt-2 border-t border-slate-850">
                    <span>Inspect Syllabus & Missions</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            );
          })}
        </section>

        {/* Track Curriculum Details Panel */}
        {selectedDomain && (
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-8 animate-fade-in">
            {(() => {
              const dom = domains.find((d) => d.id === selectedDomain);
              if (!dom) return null;
              return (
                <div>
                  <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-800">
                    <div>
                      <h4 className="text-lg font-bold text-slate-200">Missions Blueprint: {dom.name}</h4>
                      <p className="text-xs text-slate-400 mt-1">Calibrated milestone tasks and exercises</p>
                    </div>
                    <button className="bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs py-2 px-4 rounded-lg transition-all">
                      Lock In Domain Track
                    </button>
                  </div>

                  <div className="space-y-6">
                    <div className="flex items-start gap-4">
                      <div className="p-1 rounded bg-blue-500/10 text-blue-400 font-extrabold text-xs px-2.5 py-1">
                        Phase 1
                      </div>
                      <div>
                        <h5 className="font-bold text-sm text-slate-200">Foundational Discovery (Week 1–4)</h5>
                        <p className="text-xs text-slate-400 mt-1">{dom.beginner_learning_activity}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="p-1 rounded bg-indigo-500/10 text-indigo-400 font-extrabold text-xs px-2.5 py-1">
                        Phase 2
                      </div>
                      <div>
                        <h5 className="font-bold text-sm text-slate-200">System Integration & Setup (Week 5–8)</h5>
                        <p className="text-xs text-slate-400 mt-1">{dom.intermediate_learning_activity}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="p-1 rounded bg-emerald-500/10 text-emerald-400 font-extrabold text-xs px-2.5 py-1">
                        Phase 3
                      </div>
                      <div>
                        <h5 className="font-bold text-sm text-slate-200">Production Release (Week 9–12)</h5>
                        <p className="text-xs text-slate-400 mt-1">{dom.advanced_learning_activity}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </section>
        )}
      </main>
    </div>
  );
}
