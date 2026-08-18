"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpen, Users, Trophy, Code } from "lucide-react";

export default function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    // Auto redirect to dashboard if already authenticated
    const token = localStorage.getItem("accessToken");
    if (token) {
      router.push("/dashboard");
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="max-w-7xl mx-auto px-6 py-6 w-full flex justify-between items-center border-b border-slate-900">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 p-2 rounded-lg text-white font-bold">NX</div>
          <span className="font-extrabold text-xl tracking-wider">NOXUS</span>
        </div>
        <Link
          href="/login"
          className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition-all duration-200"
        >
          Sign In
        </Link>
      </header>

      {/* Hero Section */}
      <main className="max-w-4xl mx-auto px-6 py-20 text-center flex-grow flex flex-col justify-center items-center">
        <div className="inline-block bg-blue-500/10 text-blue-400 font-semibold px-4 py-1.5 rounded-full text-xs mb-6 border border-blue-500/25">
          12-Week Student-Led Technical Development
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold text-slate-100 mb-6 leading-tight max-w-3xl">
          Accelerate Your Engineering Potential.
        </h1>
        <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl leading-relaxed">
          An integrated collaboration, discovery, and student development platform. Bridge technical skill gaps through active missions, peer evaluations, and domain exploration.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 mb-20">
          <Link
            href="/login"
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-4 rounded-xl shadow-lg shadow-blue-900/30 transition-all duration-200 flex items-center gap-2 group text-base"
          >
            Enter Platform
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 w-full text-left">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
            <BookOpen className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="font-bold text-lg text-slate-200 mb-2">Roadmap</h3>
            <p className="text-sm text-slate-400">Lock-unlock mechanisms ensuring students master foundational concepts sequentially.</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
            <Code className="w-8 h-8 text-indigo-500 mb-4" />
            <h3 className="font-bold text-lg text-slate-200 mb-2">Domain Hub</h3>
            <p className="text-sm text-slate-400">A curated gallery of engineering tracks with depth tracking for career readiness.</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
            <Users className="w-8 h-8 text-emerald-500 mb-4" />
            <h3 className="font-bold text-lg text-slate-200 mb-2">Collaborate</h3>
            <p className="text-sm text-slate-400">Reciprocal review checks, technical blogs, and balanced team Capstone matching.</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
            <Trophy className="w-8 h-8 text-amber-500 mb-4" />
            <h3 className="font-bold text-lg text-slate-200 mb-2">Measure</h3>
            <p className="text-sm text-slate-400">High-fidelity metrics distinguishing personal skill progress from peer rank.</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full text-center py-8 text-slate-500 text-sm border-t border-slate-900 bg-slate-950">
        © 2026 NOXUS Bootcamp System. All rights reserved.
      </footer>
    </div>
  );
}
