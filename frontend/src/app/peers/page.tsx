"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import api from "@/lib/api";
import {
  Users, CheckCircle, Award, Send, Star, FileText, Link as LinkIcon, RefreshCw, Eye
} from "lucide-react";

export default function PeersPage() {
  const [group, setGroup] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Deliverable submission state
  const [activityId, setActivityId] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [explanationText, setExplanationText] = useState("");

  // Review teammate state
  const [selectedSubId, setSelectedSubId] = useState<string | null>(null);
  const [reviewScore, setReviewScore] = useState(5);
  const [reviewFeedback, setReviewFeedback] = useState("");
  const [isTaskReview, setIsTaskReview] = useState(false);

  // Mock pending teammate submissions for evaluation demonstration
  const [pendingReviews, setPendingReviews] = useState<any[]>([
    {
      id: "sub-101",
      student_name: "Anita Roy",
      activity_title: "Git Collaboration Exercise",
      text: "Completed branching and merged changes inside main repository. Sent PR for review.",
      evidence: "https://github.com/anita-roy/noxus/pull/3",
      is_task: false
    },
    {
      id: "sub-102",
      student_name: "Rahul Sharma",
      activity_title: "Week 2 - Binary Trees Coding Assignment",
      text: "Implemented balanced BST routines and handled recursion base cases successfully.",
      evidence: "https://github.com/rahul-sharma/trees-lab",
      is_task: true
    }
  ]);

  const fetchPeerGroup = async () => {
    try {
      const res = await api.get("/peers/my-group");
      if (res.data.success) {
        setGroup(res.data.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPeerGroup();
  }, []);

  const handleSubmitDeliverable = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      // Create mock UUID for activity if none provided
      const finalActId = activityId || "00000000-0000-0000-0000-000000000000";
      const res = await api.post("/peers/activities/submit", {
        peer_activity_id: finalActId,
        submission_text: explanationText,
        evidence_url: evidenceUrl
      });
      if (res.data.success) {
        alert("Deliverable uploaded successfully for teammate reviews!");
        setEvidenceUrl("");
        setExplanationText("");
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubId) return;
    setSubmitting(true);
    try {
      const res = await api.post("/peers/reviews/submit", {
        target_submission_id: selectedSubId,
        is_task: isTaskReview,
        review: {
          score: reviewScore,
          feedback: reviewFeedback
        }
      });
      if (res.data.success) {
        alert("Evaluation submitted! XP points awarded.");
        setPendingReviews(prev => prev.filter(r => r.id !== selectedSubId));
        setSelectedSubId(null);
        setReviewFeedback("");
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || "Verification submission failed.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading teammate group...
      </div>
    );
  }

  return (
    <div className="flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-grow p-8 max-w-6xl">
        <h1 className="text-3xl font-extrabold text-slate-100 mb-2">Peer Collaboration</h1>
        <p className="text-slate-400 text-sm mb-8 leading-relaxed">
          Coordinate deliverables with your balanced peer group. Confirm teammate task completion to trigger mutual XP bonuses.
        </p>

        {!group ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center max-w-xl">
            <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="font-extrabold text-lg text-slate-200">Awaiting Group Assignment</h3>
            <p className="text-sm text-slate-500 mt-2 leading-relaxed">
              Administrators will distribute students into skill-balanced groups during Week 2. You will receive an alert once your group allocation is complete.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Column 1: Teammates rosters */}
            <div className="space-y-6">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h3 className="font-extrabold text-base text-slate-200 mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-blue-500" />
                  {group.name}
                </h3>

                <div className="space-y-4">
                  {group.members.map((m: any, idx: number) => (
                    <div key={idx} className="bg-slate-950 border border-slate-850 p-3 rounded-xl flex justify-between items-center">
                      <div>
                        <h4 className="font-bold text-xs text-slate-200">{m.full_name}</h4>
                        <span className="text-3xs text-slate-500">Lvl {m.level} • {m.role}</span>
                      </div>
                      <div className="bg-blue-600/10 text-blue-400 text-3xs font-extrabold px-2 py-1 rounded">
                        {m.xp} XP
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Upload Deliverable form */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h3 className="font-extrabold text-base text-slate-200 mb-4">Submit Group Work</h3>
                <form onSubmit={handleSubmitDeliverable} className="space-y-3">
                  <div>
                    <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Deliverable Link</label>
                    <input
                      type="url"
                      placeholder="https://github.com/yourproject/pr/1"
                      value={evidenceUrl}
                      onChange={(e) => setEvidenceUrl(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Description / Notes</label>
                    <textarea
                      placeholder="Explain how you solved this challenge..."
                      rows={4}
                      value={explanationText}
                      onChange={(e) => setExplanationText(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 rounded-xl text-xs transition"
                  >
                    Submit Deliverables
                  </button>
                </form>
              </div>
            </div>

            {/* Column 2 & 3: Evaluator workspace */}
            <div className="md:col-span-2 space-y-6">
              
              {selectedSubId ? (
                /* Evaluate Teammate Workspace */
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
                  <div className="flex justify-between items-center pb-4 border-b border-slate-850">
                    <div>
                      <span className="text-3xs font-extrabold text-blue-500 block">EVALUATOR WORKSPACE</span>
                      <h3 className="font-bold text-base text-slate-100">Review Teammate Contribution</h3>
                    </div>
                    <button
                      onClick={() => setSelectedSubId(null)}
                      className="bg-slate-850 hover:bg-slate-800 text-slate-355 text-xs py-1 px-3 rounded-lg transition"
                    >
                      Back to list
                    </button>
                  </div>

                  {/* Submission context */}
                  <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-3">
                    <div className="flex justify-between text-2xs text-slate-500">
                      <span>Submitted by: <b>{pendingReviews.find(r => r.id === selectedSubId)?.student_name}</b></span>
                      <span>Topic: <b>{pendingReviews.find(r => r.id === selectedSubId)?.activity_title}</b></span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed font-mono">
                      {pendingReviews.find(r => r.id === selectedSubId)?.text}
                    </p>
                    <a
                      href={pendingReviews.find(r => r.id === selectedSubId)?.evidence}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:underline flex items-center gap-1 font-semibold"
                    >
                      <LinkIcon className="w-3.5 h-3.5" /> View Deliverables Evidence
                    </a>
                  </div>

                  {/* Evaluation form */}
                  <form onSubmit={handleSubmitEvaluation} className="space-y-4">
                    <div>
                      <label className="text-3xs font-bold text-slate-400 uppercase block mb-2">Score Rating</label>
                      <div className="flex gap-2">
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            key={val}
                            type="button"
                            onClick={() => setReviewScore(val)}
                            className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm border transition ${
                              reviewScore === val
                                ? "bg-blue-600 border-blue-600 text-white"
                                : "bg-slate-950 border-slate-850 text-slate-400 hover:border-slate-850"
                            }`}
                          >
                            {val}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="text-3xs font-bold text-slate-400 uppercase block mb-1">Feedback Comments</label>
                      <textarea
                        placeholder="Write constructive evaluation notes (at least 2 sentences)..."
                        rows={4}
                        value={reviewFeedback}
                        onChange={(e) => setReviewFeedback(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-xl py-2 px-3 text-xs"
                        required
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl text-xs transition"
                    >
                      Verify and Award XP Points
                    </button>
                  </form>
                </div>
              ) : (
                /* List of Pending Reviews */
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h3 className="font-extrabold text-base text-slate-200 mb-4">Teammate Evaluations Queue</h3>
                  
                  <div className="space-y-4">
                    {pendingReviews.length > 0 ? (
                      pendingReviews.map((rev) => (
                        <div
                          key={rev.id}
                          className="bg-slate-950 border border-slate-850 p-4 rounded-xl flex justify-between items-center hover:border-slate-800 transition"
                        >
                          <div>
                            <span className="text-3xs text-blue-500 font-extrabold uppercase">
                              {rev.is_task ? "TASK SUBMISSION" : "PEER ACTIVITY"}
                            </span>
                            <h4 className="font-bold text-sm text-slate-200 mt-1">{rev.activity_title}</h4>
                            <p className="text-2xs text-slate-400 mt-0.5">Submitted by: {rev.student_name}</p>
                          </div>
                          
                          <button
                            onClick={() => {
                              setSelectedSubId(rev.id);
                              setIsTaskReview(rev.is_task);
                            }}
                            className="bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 font-bold py-2 px-4 rounded-lg text-xs transition flex items-center gap-1.5"
                          >
                            <Eye className="w-4 h-4" /> Evaluate
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="text-slate-500 text-xs text-center py-6">All teammate reviews are resolved. Good job!</p>
                    )}
                  </div>
                </div>
              )}

            </div>
          </div>
        )}
      </div>
    </div>
  );
}
