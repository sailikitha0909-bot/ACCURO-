"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/common/Logo";
import { apiFetch, setAuthSession } from "@/lib/api";
import { ShieldCheck, UserCheck, Lock, Mail, ArrowRight, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("partner@mehta-ca.in");
  const [password, setPassword] = useState("Partner@Accuro2025!");
  const [totpCode, setTotpCode] = useState("");
  const [requireTotp, setRequireTotp] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await apiFetch<any>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          password,
          totp_code: totpCode.trim() || undefined,
        }),
      });

      setAuthSession(res.access_token, res.user);
      router.push("/");
    } catch (err: any) {
      if (err.message && err.message.includes("2FA_REQUIRED")) {
        setRequireTotp(true);
      } else {
        setErrorMsg(err.message || "Invalid email or password");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setIsLoading(true);
    setErrorMsg("");

    apiFetch<any>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: demoEmail, password: demoPass }),
    })
      .then((res) => {
        setAuthSession(res.access_token, res.user);
        router.push("/");
      })
      .catch((err) => {
        setErrorMsg(err.message || "Login failed");
      })
      .finally(() => setIsLoading(false));
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4 selection:bg-blue-600 selection:text-white">
      {/* Container */}
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl p-8 border border-slate-200">
          {/* Brand Wordmark & Tagline */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-2">
              <Logo size="lg" />
            </div>
            <p className="text-xs text-slate-500 font-normal mt-1">
              Accurate accounts. You review, Accuro does the rest.
            </p>
          </div>

          {errorMsg && (
            <div className="mb-5 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Firm Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@firm-ca.in"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>
            </div>

            {requireTotp && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  6-Digit 2FA Authenticator Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  placeholder="123456"
                  className="w-full px-3 py-2 text-xs font-mono tracking-widest text-center border border-blue-400 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-[#1E3A8A] hover:bg-blue-900 active:scale-[0.99] text-white text-xs font-semibold rounded-lg shadow transition-all flex items-center justify-center gap-2"
            >
              <span>{isLoading ? "Authenticating..." : "Sign in to Firm Console"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Quick Demo Logins for Reviewers */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center mb-3">
              1-Click Demo Accounts (Pre-Seeded)
            </p>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => loginAsDemo("partner@mehta-ca.in", "Partner@Accuro2025!")}
                className="p-2.5 text-left border border-blue-200 bg-blue-50/70 hover:bg-blue-100/70 rounded-lg transition-colors group"
              >
                <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-700" />
                  <span>CA Partner</span>
                </div>
                <p className="text-[10px] text-blue-700 mt-0.5">Approval & export rights</p>
              </button>

              <button
                type="button"
                onClick={() => loginAsDemo("article@mehta-ca.in", "Article@Accuro2025!")}
                className="p-2.5 text-left border border-slate-200 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors group"
              >
                <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                  <UserCheck className="w-3.5 h-3.5 text-slate-600" />
                  <span>Article Staff</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">Review & drafting rights</p>
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-[11px] text-slate-500 mt-6">
          Accuro • Multi-tenant CA Firm Automation Platform
        </p>
      </div>
    </div>
  );
}
