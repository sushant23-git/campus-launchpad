"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import api from "../../lib/api";
import {
  FolderKanban, Award, Clock, CheckCircle, Plus, Eye, Send, Link as LinkIcon, AlertCircle, RefreshCw
} from "lucide-react";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [myTeam, setMyTeam] = useState<any>(null);
  const [milestones, setMilestones] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Team formation inputs
  const [teamName, setTeamName] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  
  // Teammates picker inputs (simple comma separated lists of teammate user IDs for demonstration)
  // In a full implementation, this uses searchable dropdowns
  const [teammateIds, setTeammateIds] = useState("");
  const [teammateRoles, setTeammateRoles] = useState("");

  // Milestone submission inputs
  const [selectedMilestoneId, setSelectedMilestoneId] = useState<string | null>(null);
  const [deliveryUrl, setDeliveryUrl] = useState("");
  const [githubPrUrl, setGithubPrUrl] = useState("");

  const fetchProjectsData = async () => {
    try {
      const res = await api.get("/projects");
      if (res.data.success) {
        setProjects(res.data.data);
      }
      
      // Let's check if user is on a project team (simulated or via /peers/my-group mapping)
      // For projects, we check if student is assigned. If not, they build one.
      // We can query team details. If none found, we present the team builder.
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectsData();
  }, []);

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      // Parse teammate IDs and roles into dict
      const idArray = teammateIds.split(",").map(id => id.trim()).filter(Boolean);
      const roleArray = teammateRoles.split(",").map(r => r.trim()).filter(Boolean);
      
      if (idArray.length < 3 || idArray.length > 5) {
        alert("Teammate count must be between 3 and 5 (making 4-6 members total including yourself).");
        setSubmitting(false);
        return;
      }

      const rolesDict: Record<string, string> = {};
      idArray.forEach((id, idx) => {
        rolesDict[id] = roleArray[idx] || "Developer";
      });

      const res = await api.post("/projects/teams/create", {
        project_id: selectedProjectId,
        team_name: teamName,
        cohort_id: "00000000-0000-0000-0000-000000000000", // Default fallback cohort UUID
        members_roles: rolesDict
      });

      if (res.data.success) {
        alert("Project team formed successfully! Milestones unlocked.");
        setMyTeam(res.data.data);
        // Fetch milestones
        const milRes = await api.get(`/projects/milestones?project_id=${selectedProjectId}`);
        if (milRes.data.success) {
          setMilestones(milRes.data.data);
        }
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || "Failed to form team. Verify size limits.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMilestoneId || !myTeam) return;
    setSubmitting(true);

    try {
      const res = await api.post("/projects/milestones/submit", {
        project_team_id: myTeam.id,
        milestone_id: selectedMilestoneId,
        submission_url: deliveryUrl,
        github_pr_url: githubPrUrl
      });

      if (res.data.success) {
        alert("Milestone deliverables uploaded! Pending evaluator reviews.");
        setSelectedMilestoneId(null);
        setDeliveryUrl("");
        setGithubPrUrl("");
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || "Milestone upload failed.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading collaborative workspace...
      </div>
    );
  }

  return (
    <div className="flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-grow p-8 max-w-6xl">
        <h1 className="text-3xl font-extrabold text-slate-100 mb-2">Industry Project Teams</h1>
        <p className="text-slate-400 text-sm mb-8 leading-relaxed">
          Form self-led teams of 4–6 students to tackle industry problems. Milestone grading awards XP collectively.
        </p>

        {!myTeam ? (
          /* State 1: Team builder and Projects list */
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Project List */}
            <div className="md:col-span-2 space-y-6">
              <h3 className="font-extrabold text-base text-slate-200">Explore Anonymized Problem Statements</h3>
              
              <div className="space-y-4">
                {projects.map((p) => (
                  <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-3xs font-extrabold text-blue-500 uppercase tracking-wider block">ID: {p.project_code}</span>
                        <h4 className="font-bold text-sm text-slate-200 mt-1">{p.title}</h4>
                      </div>
                      <span className="text-3xs font-extrabold bg-slate-800 text-slate-400 px-2 py-1 rounded">
                        {p.difficulty}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed font-mono">{p.description}</p>
                    <div className="flex items-center gap-2 pt-2 text-3xs font-semibold text-slate-500">
                      <span>Source: <b>{p.problem_source_type}</b></span>
                      <span>•</span>
                      <span>Domain: <b>{p.domain}</b></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Team builder form */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-fit">
              <h3 className="font-extrabold text-base text-slate-200 mb-4 flex items-center gap-2">
                <FolderKanban className="w-5 h-5 text-blue-500" />
                Team Builder
              </h3>
              
              <form onSubmit={handleCreateTeam} className="space-y-4">
                <div>
                  <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Pick Project ID</label>
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                    required
                  >
                    <option value="">Select Project...</option>
                    {projects.map(p => (
                      <option key={p.id} value={p.id}>{p.project_code} - {p.title}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Team Name</label>
                  <input
                    type="text"
                    placeholder="NoXus Builders"
                    value={teamName}
                    onChange={(e) => setTeamName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                    required
                  />
                </div>

                <div>
                  <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">
                    Teammate User IDs (comma separated)
                  </label>
                  <textarea
                    placeholder="uuid-1, uuid-2, uuid-3"
                    rows={2}
                    value={teammateIds}
                    onChange={(e) => setTeammateIds(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                    required
                  />
                </div>

                <div>
                  <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">
                    Teammate Roles (comma separated)
                  </label>
                  <textarea
                    placeholder="Frontend, Backend, Designer"
                    rows={2}
                    value={teammateRoles}
                    onChange={(e) => setTeammateRoles(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl text-xs transition"
                >
                  Create Project Team
                </button>
              </form>
            </div>

          </div>
        ) : (
          /* State 2: Milestones list & submission workspces */
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Milestones Roadmap list */}
            <div className="md:col-span-2 space-y-6">
              <h3 className="font-extrabold text-base text-slate-200">Weekly Deliverables Milestone Roadmap</h3>
              
              <div className="space-y-4">
                {milestones.length > 0 ? (
                  milestones.map((mil) => (
                    <div
                      key={mil.id}
                      className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex justify-between items-center hover:border-slate-700 transition"
                    >
                      <div>
                        <span className="text-3xs font-extrabold text-blue-500 block">MILESTONE {mil.week_number}</span>
                        <h4 className="font-bold text-sm text-slate-200 mt-1">{mil.title}</h4>
                        <p className="text-2xs text-slate-400 mt-0.5 leading-relaxed">{mil.description}</p>
                      </div>

                      <button
                        onClick={() => setSelectedMilestoneId(mil.id)}
                        className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded-lg text-xs transition"
                      >
                        Submit Delivery
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 text-xs">No milestones configured for this project statement.</p>
                )}
              </div>
            </div>

            {/* Submission dialog column */}
            <div className="space-y-6">
              {selectedMilestoneId && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                  <h3 className="font-extrabold text-base text-slate-200 mb-4">Upload Deliverables</h3>
                  <form onSubmit={handleSubmitMilestone} className="space-y-4">
                    <div>
                      <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Production Demo URL</label>
                      <input
                        type="url"
                        placeholder="https://my-app.vercel.app"
                        value={deliveryUrl}
                        onChange={(e) => setDeliveryUrl(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-855 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">GitHub Pull Request URL</label>
                      <input
                        type="url"
                        placeholder="https://github.com/my-repo/pull/5"
                        value={githubPrUrl}
                        onChange={(e) => setGithubPrUrl(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-855 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                        required
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-xl text-xs transition flex items-center justify-center gap-2"
                    >
                      {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Send Delivery Details"}
                    </button>
                  </form>
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
