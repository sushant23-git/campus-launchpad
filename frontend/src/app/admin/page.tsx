"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import api from "@/lib/api";
import {
  ShieldAlert, Download, Award, Users, AlertTriangle, RefreshCw, CheckCircle, Flame
} from "lucide-react";

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // XP adjustment inputs
  const [studentId, setStudentId] = useState("");
  const [xpAdjustment, setXpAdjustment] = useState("");
  const [adjustmentReason, setAdjustmentReason] = useState("");

  // Simulated list of student risk warning flags for demonstration
  const [riskFlags, setRiskFlags] = useState<any[]>([
    {
      id: "rf-101",
      student_name: "Vikram Malhotra",
      risk_level: "High",
      reason: "Inactivity detected for 9 consecutive days.",
      intervention: "Reach out via email or Discord to verify availability."
    },
    {
      id: "rf-102",
      student_name: "Pooja Hegde",
      risk_level: "Medium",
      reason: "Assessment grades avg trailing below 45% standard.",
      intervention: "Recommend tutoring hours or schedule mentor 1-on-1 review."
    }
  ]);

  const cohortId = "00000000-0000-0000-0000-000000000000"; // default fallback uuid

  const fetchAdminStats = async () => {
    try {
      const res = await api.get(`/admin/analytics?cohort_id=${cohortId}`);
      if (res.data.success) {
        setStats(res.data.data);
      }
    } catch (err) {
      console.error("Admin stats fetch error", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminStats();
  }, []);

  const handleManualXpOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.post("/admin/xp/adjust", {
        student_id: studentId,
        points: parseInt(xpAdjustment),
        reason: adjustmentReason
      });

      if (res.data.success) {
        alert("Student XP successfully adjusted and logged to audit trail!");
        setStudentId("");
        setXpAdjustment("");
        setAdjustmentReason("");
        fetchAdminStats();
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || "Adjustment failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleExportStudents = () => {
    window.open(`http://localhost:8000/api/v1/admin/export/students?cohort_id=${cohortId}`);
  };

  const handleExportSubmissions = () => {
    window.open(`http://localhost:8000/api/v1/admin/export/submissions?cohort_id=${cohortId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading admin console...
      </div>
    );
  }

  const overallStats = stats || {
    total_students: 242,
    active_students: 218,
    average_xp: 412.5,
    average_progress: 72.8,
    submission_backlog: 12,
    at_risk_students: 2
  };

  return (
    <div className="flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-grow p-8 max-w-6xl space-y-8">
        
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="w-8 h-8 text-indigo-500" />
              Admin Console & Overrides
            </h1>
            <p className="text-slate-400 text-sm mt-1">Audit student performance, trigger warnings, and export rosters.</p>
          </div>

          {/* Export buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleExportStudents}
              className="bg-slate-900 border border-slate-800 hover:bg-slate-855 text-slate-200 py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center gap-1.5"
            >
              <Download className="w-4 h-4" /> Export Student Grades CSV
            </button>
            <button
              onClick={handleExportSubmissions}
              className="bg-slate-900 border border-slate-800 hover:bg-slate-855 text-slate-200 py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center gap-1.5"
            >
              <Download className="w-4 h-4" /> Export Task Log CSV
            </button>
          </div>
        </div>

        {/* Aggregated Analytics Dashboard Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
            <span className="text-slate-400 text-3xs font-extrabold uppercase tracking-wider block">COHORT ENROLLMENT</span>
            <span className="text-2xl font-black text-slate-100 block mt-1">{overallStats.total_students} Students</span>
            <span className="text-3xs text-emerald-400 font-semibold mt-1 block">Active logins: {overallStats.active_students}</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
            <span className="text-slate-400 text-3xs font-extrabold uppercase tracking-wider block">AVERAGE CUMULATIVE XP</span>
            <span className="text-2xl font-black text-blue-400 block mt-1">{overallStats.average_xp} XP</span>
            <span className="text-3xs text-slate-500 font-semibold mt-1 block">Level target index: 3.2</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
            <span className="text-slate-400 text-3xs font-extrabold uppercase tracking-wider block">CURRICULUM SYLLABUS AVG</span>
            <span className="text-2xl font-black text-indigo-400 block mt-1">{overallStats.average_progress}%</span>
            <span className="text-3xs text-slate-550 font-semibold mt-1 block">Tasks done target: 80%</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
            <span className="text-slate-400 text-3xs font-extrabold uppercase tracking-wider block">SUBMISSION BACKLOG</span>
            <span className="text-2xl font-black text-orange-500 block mt-1">{overallStats.submission_backlog} Items</span>
            <span className="text-3xs text-slate-550 font-semibold mt-1 block">Pending mentor evaluation</span>
          </div>
        </div>

        {/* Grid: XP override and Risk flags table */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Risk warning flags table */}
          <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h3 className="font-extrabold text-base text-slate-200 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              At-Risk Student Alerts
            </h3>
            
            <div className="space-y-4">
              {riskFlags.length > 0 ? (
                riskFlags.map((flag) => (
                  <div key={flag.id} className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="font-bold text-xs text-slate-200">{flag.student_name}</h4>
                      <span className={`text-3xs font-extrabold px-2 py-0.5 rounded uppercase ${
                        flag.risk_level === "High" ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-orange-500/10 text-orange-400 border border-orange-500/20"
                      }`}>
                        {flag.risk_level} Risk
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed font-mono">{flag.reason}</p>
                    <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-855 text-3xs text-blue-400 leading-relaxed">
                      <b>Intervention:</b> {flag.intervention}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 text-xs py-4 text-center">No students flagged as at-risk. Great job!</p>
              )}
            </div>
          </div>

          {/* XP manual adjustment form */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-fit">
            <h3 className="font-extrabold text-base text-slate-200 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-500" />
              Manual XP Adjustments
            </h3>
            
            <form onSubmit={handleManualXpOverride} className="space-y-4">
              <div>
                <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Student User ID</label>
                <input
                  type="text"
                  placeholder="uuid-format-here"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-855 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">XP Points (+ / -)</label>
                <input
                  type="number"
                  placeholder="e.g. 200 or -100"
                  value={xpAdjustment}
                  onChange={(e) => setXpAdjustment(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-855 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Reason for override</label>
                <textarea
                  placeholder="Reason for manually adjusting student points score..."
                  rows={3}
                  value={adjustmentReason}
                  onChange={(e) => setAdjustmentReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-855 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-xl text-xs transition"
              >
                Apply Overrides
              </button>
            </form>
          </div>

        </div>

      </div>
    </div>
  );
}
