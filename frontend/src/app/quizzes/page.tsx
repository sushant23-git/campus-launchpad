"use client";

import React, { useEffect, useState, useRef } from "react";
import Sidebar from "../../components/Sidebar";
import api from "../../lib/api";
import {
  Award, Clock, CheckCircle, AlertTriangle, Play, RefreshCw, XCircle, ArrowRight
} from "lucide-react";

export default function QuizzesPage() {
  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [activeAttempt, setActiveAttempt] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string[]>>({});
  const [timeLeft, setTimeLeft] = useState(0); // in seconds
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Timer refs
  const quizTimer = useRef<NodeJS.Timeout | null>(null);
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null);

  const fetchQuizzes = async () => {
    try {
      const res = await api.get("/quizzes");
      if (res.data.success) {
        setQuizzes(res.data.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuizzes();
    return () => {
      clearTimers();
    };
  }, []);

  const clearTimers = () => {
    if (quizTimer.current) clearInterval(quizTimer.current);
    if (autoSaveTimer.current) clearInterval(autoSaveTimer.current);
  };

  const handleStartQuiz = async (quizId: string) => {
    setLoading(true);
    try {
      const res = await api.post(`/quizzes/${quizId}/start`);
      if (res.data.success) {
        const { attempt, questions } = res.data.data;
        setActiveAttempt(attempt);
        setQuestions(questions);

        // Reset answers
        setSelectedAnswers({});

        // Set time limit countdown
        const minutes = attempt.quiz_title ? 15 : 20; // default backup
        // Or calculate from attempt started_at
        const timeLimitSec = (attempt.quiz?.time_limit_minutes || 20) * 60;
        const elapsedSec = Math.floor((Date.now() - new Date(attempt.started_at).getTime()) / 1000);
        const remaining = Math.max(0, timeLimitSec - elapsedSec);
        setTimeLeft(remaining);

        // Start countdown
        quizTimer.current = setInterval(() => {
          setTimeLeft(prev => {
            if (prev <= 1) {
              clearTimers();
              handleAutoSubmit();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);

        // Start 30s autosave loop
        autoSaveTimer.current = setInterval(() => {
          handleSaveAnswers();
        }, 30000);
      }
    } catch (err) {
      console.error("Failed to start quiz", err);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionChange = (questionId: string, optionValue: string, isMultiple = false) => {
    setSelectedAnswers(prev => {
      const current = prev[questionId] || [];
      if (isMultiple) {
        if (current.includes(optionValue)) {
          return { ...prev, [questionId]: current.filter(o => o !== optionValue) };
        } else {
          return { ...prev, [questionId]: [...current, optionValue] };
        }
      } else {
        return { ...prev, [questionId]: [optionValue] };
      }
    });
  };

  const handleSaveAnswers = async () => {
    if (!activeAttempt) return;
    try {
      const answersPayload = Object.entries(selectedAnswers).map(([qid, options]) => ({
        question_id: qid,
        selected_options: options
      }));
      await api.post(`/quizzes/attempts/${activeAttempt.id}/save`, {
        answers: answersPayload
      });
    } catch (err) {
      console.error("Autosave answers error", err);
    }
  };

  const handleAutoSubmit = () => {
    handleSubmitQuiz(true);
  };

  const handleSubmitQuiz = async (isAuto = false) => {
    if (!activeAttempt || submitting) return;
    setSubmitting(true);
    clearTimers();
    
    // Save any final answers first
    await handleSaveAnswers();

    try {
      const answersPayload = Object.entries(selectedAnswers).map(([qid, options]) => ({
        question_id: qid,
        selected_options: options
      }));

      const res = await api.post("/quizzes/attempts/submit", {
        attempt_id: activeAttempt.id,
        answers: answersPayload
      });

      if (res.data.success) {
        alert(isAuto ? "Time limit exceeded. Quiz auto-submitted." : "Quiz evaluated successfully!");
        setActiveAttempt(null);
        setQuestions([]);
        fetchQuizzes();
      }
    } catch (err) {
      console.error("Submit quiz error", err);
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    return `${min}:${sec < 10 ? "0" : ""}${sec}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading assessment portal...
      </div>
    );
  }

  return (
    <div className="flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-grow p-8 max-w-6xl">
        {activeAttempt ? (
          /* Active Timed Quiz Player screen */
          <div className="space-y-6 max-w-3xl mx-auto">
            <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-5 rounded-2xl sticky top-4 z-10">
              <div>
                <span className="text-3xs font-extrabold text-blue-500 block">TIMED ASSESSMENT IN PROGRESS</span>
                <h2 className="text-xl font-bold text-slate-200">Solving Week Quiz</h2>
              </div>
              <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-4 py-2.5 rounded-xl font-mono text-xl font-black text-orange-500">
                <Clock className="w-5 h-5 text-orange-500 animate-pulse" />
                <span>{formatTime(timeLeft)}</span>
              </div>
            </div>

            <div className="space-y-6">
              {questions.map((q, idx) => {
                const selections = selectedAnswers[q.id] || [];
                const isMulti = q.question_type === "MSQ";
                
                return (
                  <div key={q.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <div className="flex justify-between items-start">
                      <span className="text-xs text-blue-500 font-extrabold">QUESTION {idx + 1} ({q.marks} pts)</span>
                      <span className="text-3xs font-extrabold bg-slate-800 px-2 py-1 rounded text-slate-400 uppercase">
                        {q.question_type.replace("_", " ")}
                      </span>
                    </div>

                    <p className="text-sm font-bold text-slate-200 leading-relaxed">{q.question_text}</p>

                    <div className="space-y-2 pt-2">
                      {q.options.map((opt: string, optIdx: number) => {
                        const checked = selections.includes(opt);
                        return (
                          <div
                            key={optIdx}
                            onClick={() => handleOptionChange(q.id, opt, isMulti)}
                            className={`flex items-center gap-3 border p-3 rounded-xl cursor-pointer transition ${
                              checked 
                                ? "bg-blue-600/10 border-blue-600/80 text-blue-300 font-semibold" 
                                : "bg-slate-950 border-slate-850 text-slate-400 hover:border-slate-800"
                            }`}
                          >
                            <input
                              type={isMulti ? "checkbox" : "radio"}
                              checked={checked}
                              readOnly
                              className="accent-blue-600"
                            />
                            <span className="text-xs">{opt}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            <button
              onClick={() => handleSubmitQuiz(false)}
              disabled={submitting}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-2xl transition flex items-center justify-center gap-2 mt-4"
            >
              {submitting ? <RefreshCw className="w-5 h-5 animate-spin" /> : "Finish & Submit Quiz"}
            </button>
          </div>
        ) : (
          /* Quizzes List screen */
          <div>
            <h1 className="text-3xl font-extrabold text-slate-100 mb-2">Assessments Portal</h1>
            <p className="text-slate-400 text-sm mb-8 leading-relaxed">
              Verify your comprehension of modules. Ensure you complete quizzes within time constraints.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {quizzes.map((quiz) => {
                const isLocked = quiz.is_locked;
                
                return (
                  <div
                    key={quiz.id}
                    className={`bg-slate-900 border rounded-2xl p-6 flex flex-col justify-between transition ${
                      isLocked ? "border-slate-900/60 opacity-60" : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start mb-4">
                        <span className="text-2xs font-extrabold text-blue-500 uppercase">WEEK ASSESSMENT</span>
                        {quiz.completed_attempts > 0 ? (
                          <span className="flex items-center gap-1 text-2xs font-extrabold text-emerald-500">
                            <CheckCircle className="w-4 h-4 text-emerald-500" /> PASS
                          </span>
                        ) : (
                          isLocked && (
                            <span className="flex items-center gap-1 text-2xs font-extrabold text-red-400">
                              <XCircle className="w-4 h-4 text-red-500" /> LOCKED
                            </span>
                          )
                        )}
                      </div>

                      <h3 className="font-extrabold text-lg text-slate-200 mb-2">{quiz.title}</h3>
                      <p className="text-xs text-slate-400 leading-relaxed mb-4">{quiz.description}</p>

                      <div className="flex items-center gap-4 text-3xs font-semibold text-slate-500 mb-6">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" /> {quiz.time_limit_minutes} Mins
                        </span>
                        <span>•</span>
                        <span>Passing Score: {quiz.passing_score}%</span>
                        <span>•</span>
                        <span>Attempts Left: {quiz.attempts_remaining}</span>
                      </div>
                    </div>

                    {isLocked ? (
                      <div className="bg-red-500/10 border border-red-500/15 text-red-400 text-2xs p-3 rounded-xl flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Locked: {quiz.lock_reason}</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleStartQuiz(quiz.id)}
                        disabled={quiz.attempts_remaining === 0}
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition text-xs flex items-center justify-center gap-2"
                      >
                        <Play className="w-4 h-4 fill-current" /> Start Timed Quiz
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
