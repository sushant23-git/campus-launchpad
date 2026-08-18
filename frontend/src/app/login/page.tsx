"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, Mail, User as UserIcon, RefreshCw, KeyRound, Award, BookOpen } from "lucide-react";
import api from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // Onboarding Profile state
  const [needOnboarding, setNeedOnboarding] = useState(false);
  const [fullName, setFullName] = useState("");
  const [collegeName, setCollegeName] = useState("");
  const [branch, setBranch] = useState("");
  const [year, setYear] = useState("First Year");
  const [skills, setSkills] = useState("");

  // 2FA OTP state
  const [needOTP, setNeedOTP] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [tempUserId, setTempUserId] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      if (isRegister) {
        // Register Student
        if (password !== confirmPassword) {
          setErrorMsg("Passwords do not match.");
          setLoading(false);
          return;
        }

        const res = await api.post("/auth/register", { email, password });
        if (res.data.success) {
          setSuccessMsg("Registration successful! Please sign in using your credentials.");
          setIsRegister(false);
          setPassword("");
          setConfirmPassword("");
        }
      } else {
        // Login
        const res = await api.post("/auth/login", { email, password });
        if (res.data.success) {
          const { require_2fa, user_id, access_token, refresh_token } = res.data.data;
          
          if (require_2fa) {
            setNeedOTP(true);
            setTempUserId(user_id);
          } else {
            // Save tokens
            localStorage.setItem("accessToken", access_token);
            localStorage.setItem("refreshToken", refresh_token);
            
            // Check if profile onboarding is complete
            const meRes = await api.get("/auth/me");
            const profile = meRes.data.data.profile;
            
            if (!profile || !profile.profile_completed) {
              setNeedOnboarding(true);
            } else {
              router.push("/dashboard");
            }
          }
        }
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error?.message || "Operation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    try {
      const res = await api.post("/auth/verify-2fa", {
        user_id: tempUserId,
        code: otpCode,
      });

      if (res.data.success) {
        const { access_token, refresh_token } = res.data.data;
        localStorage.setItem("accessToken", access_token);
        localStorage.setItem("refreshToken", refresh_token);
        
        router.push("/dashboard");
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error?.message || "Invalid 2FA passcode code.");
    } finally {
      setLoading(false);
    }
  };

  const handleOnboardingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    try {
      const skillsArray = skills.split(",").map(s => s.trim()).filter(Boolean);
      const res = await api.post("/auth/onboard", {
        full_name: fullName,
        college_name: collegeName,
        branch: branch,
        year: year,
        skills: skillsArray,
        interests: []
      });

      if (res.data.success) {
        router.push("/dashboard");
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error?.message || "Failed to update profile onboarding.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-slate-100">
      {/* Brand Header */}
      <div className="flex items-center gap-2 mb-8">
        <div className="bg-blue-600 p-2.5 rounded-xl text-white font-bold text-xl">NX</div>
        <span className="font-extrabold text-2xl tracking-wider">NOXUS</span>
      </div>

      {/* Main card wrapper */}
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        
        {/* State 1: 2FA Passcode Verification Overlay */}
        {needOTP && (
          <form onSubmit={handleVerifyOTP} className="space-y-6 animate-fade-in">
            <div className="text-center">
              <KeyRound className="w-12 h-12 text-blue-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold">Staff 2FA Verification</h2>
              <p className="text-sm text-slate-400 mt-2">
                Enter the 6-digit verification code from your Google Authenticator App.
              </p>
            </div>

            {errorMsg && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm text-center">
                {errorMsg}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">OTP Code</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 text-slate-500 w-5 h-5" />
                <input
                  type="text"
                  maxLength={6}
                  placeholder="000000"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-3.5 pl-12 pr-4 text-center font-mono text-lg tracking-widest"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3.5 rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : "Verify & Continue"}
            </button>
          </form>
        )}

        {/* State 2: Profile Onboarding Setup Modal */}
        {needOnboarding && (
          <form onSubmit={handleOnboardingSubmit} className="space-y-5 animate-fade-in">
            <div className="text-center">
              <Award className="w-12 h-12 text-blue-500 mx-auto mb-3" />
              <h2 className="text-2xl font-bold">Complete Your Profile</h2>
              <p className="text-xs text-slate-400 mt-1">
                Tell us about your background to calibrate your learning path.
              </p>
            </div>

            {errorMsg && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm text-center">
                {errorMsg}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Full Name</label>
                <input
                  type="text"
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-2.5 px-4 text-sm"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">College Name</label>
                <input
                  type="text"
                  placeholder="Indian Institute of Technology"
                  value={collegeName}
                  onChange={(e) => setCollegeName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-2.5 px-4 text-sm"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Department</label>
                  <input
                    type="text"
                    placeholder="Computer Science"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-2.5 px-4 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Year</label>
                  <select
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-2.5 px-4 text-sm"
                  >
                    <option value="First Year">First Year</option>
                    <option value="Second Year">Second Year</option>
                    <option value="Third Year">Third Year</option>
                    <option value="Fourth Year">Fourth Year</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Skills (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="Python, Git, HTML, React"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-2.5 px-4 text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 mt-2"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : "Save Profile & Start Learning"}
            </button>
          </form>
        )}

        {/* State 3: Normal Authentication Form */}
        {!needOTP && !needOnboarding && (
          <form onSubmit={handleAuth} className="space-y-6">
            <div className="flex border-b border-slate-800 mb-6">
              <button
                type="button"
                onClick={() => { setIsRegister(false); setErrorMsg(""); setSuccessMsg(""); }}
                className={`w-1/2 pb-4 font-bold text-sm tracking-wider transition ${
                  !isRegister ? "border-b-2 border-blue-500 text-slate-100" : "text-slate-500"
                }`}
              >
                SIGN IN
              </button>
              <button
                type="button"
                onClick={() => { setIsRegister(true); setErrorMsg(""); setSuccessMsg(""); }}
                className={`w-1/2 pb-4 font-bold text-sm tracking-wider transition ${
                  isRegister ? "border-b-2 border-blue-500 text-slate-100" : "text-slate-500"
                }`}
              >
                REGISTER
              </button>
            </div>

            {errorMsg && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl text-sm text-center">
                {errorMsg}
              </div>
            )}

            {successMsg && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-3 rounded-xl text-sm text-center">
                {successMsg}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3.5 text-slate-500 w-4 h-4" />
                  <input
                    type="email"
                    placeholder="student@example.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-3 pl-10 pr-4 text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3.5 text-slate-500 w-4 h-4" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-3 pl-10 pr-4 text-sm"
                    required
                  />
                </div>
              </div>

              {isRegister && (
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3.5 text-slate-500 w-4 h-4" />
                    <input
                      type="password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-3 pl-10 pr-4 text-sm"
                      required
                    />
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3.5 rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (isRegister ? "Create Student Account" : "Sign In")}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
