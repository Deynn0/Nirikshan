import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, User, Building, CheckCircle2, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('officer.aicte');
  const [role, setRole] = useState<'applicant' | 'officer'>('officer');
  const [institutionId, setInstitutionId] = useState('INST-DELHI-098');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, role, role === 'applicant' ? institutionId : undefined);
      if (role === 'applicant') {
        navigate('/applicant');
      } else {
        navigate('/officer');
      }
    } catch (err: any) {
      setError(err?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (selectedRole: 'applicant' | 'officer') => {
    setRole(selectedRole);
    const user = selectedRole === 'applicant' ? 'registrar.iitdelhi' : 'officer.scrutiny1';
    setUsername(user);
    setLoading(true);
    try {
      await login(user, selectedRole, selectedRole === 'applicant' ? 'INST-IITD-001' : undefined);
      navigate(selectedRole === 'applicant' ? '/applicant' : '/officer');
    } catch (err: any) {
      setError(err?.message || 'Quick login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 relative overflow-hidden bg-slate-950">
      {/* Background Glow Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Branding Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-600 via-indigo-600 to-purple-600 p-0.5 shadow-xl shadow-sky-500/25 mb-4">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <Shield className="w-8 h-8 text-sky-400" />
            </div>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Nirikshan <span className="text-sky-400 font-hindi">(निरीक्षण)</span>
          </h1>
          <p className="mt-2 text-sm text-slate-400 max-w-xs mx-auto">
            {t('auth.subtitle')} — AICTE Approval Process Handbook Compliance
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel rounded-2xl p-6 sm:p-8 shadow-2xl border border-slate-800">
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-rose-950/50 border border-rose-500/30 text-rose-200 text-xs flex items-center gap-2">
              <span className="font-semibold">Error:</span> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Role Picker */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                {t('auth.role')}
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setRole('officer')}
                  className={`p-3 rounded-xl border text-left transition-all flex flex-col gap-1 ${
                    role === 'officer'
                      ? 'bg-indigo-950/60 border-indigo-500/60 ring-2 ring-indigo-500/30 text-white'
                      : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <ShieldCheck className={`w-4 h-4 ${role === 'officer' ? 'text-indigo-400' : 'text-slate-500'}`} />
                    {role === 'officer' && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />}
                  </div>
                  <span className="text-xs font-bold mt-1 text-slate-200">{t('auth.officerRole')}</span>
                  <span className="text-[10px] text-slate-400">Scrutiny & Evidence Audit</span>
                </button>

                <button
                  type="button"
                  onClick={() => setRole('applicant')}
                  className={`p-3 rounded-xl border text-left transition-all flex flex-col gap-1 ${
                    role === 'applicant'
                      ? 'bg-sky-950/60 border-sky-500/60 ring-2 ring-sky-500/30 text-white'
                      : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <Building className={`w-4 h-4 ${role === 'applicant' ? 'text-sky-400' : 'text-slate-500'}`} />
                    {role === 'applicant' && <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />}
                  </div>
                  <span className="text-xs font-bold mt-1 text-slate-200">{t('auth.applicantRole')}</span>
                  <span className="text-[10px] text-slate-400">Upload & Self-Check</span>
                </button>
              </div>
            </div>

            {/* Username / ID */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                {t('auth.username')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl glass-input text-sm text-white placeholder-slate-500 transition-colors"
                  placeholder="e.g. officer.aicte or inst.registrar"
                />
              </div>
            </div>

            {/* Institution ID (if applicant) */}
            {role === 'applicant' && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  AICTE Permanent Institute ID
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Building className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={institutionId}
                    onChange={(e) => setInstitutionId(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl glass-input text-sm text-white placeholder-slate-500 transition-colors"
                    placeholder="e.g. 1-123456789"
                  />
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-500 via-indigo-600 to-purple-600 hover:from-sky-400 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-sky-500/20 hover:shadow-sky-500/40 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>{t('auth.loginBtn')}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Login Bar */}
          <div className="mt-6 pt-5 border-t border-slate-800">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                {t('auth.quickLogin')}
              </span>
              <span className="text-[10px] text-amber-400/80 font-mono">1-Click Test</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('officer')}
                className="py-2 px-3 rounded-lg bg-indigo-950/40 hover:bg-indigo-900/50 border border-indigo-500/30 text-xs font-medium text-indigo-200 transition-colors flex items-center justify-center gap-1.5"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                <span>AICTE Officer</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('applicant')}
                className="py-2 px-3 rounded-lg bg-sky-950/40 hover:bg-sky-900/50 border border-sky-500/30 text-xs font-medium text-sky-200 transition-colors flex items-center justify-center gap-1.5"
              >
                <Building className="w-3.5 h-3.5 text-sky-400" />
                <span>Applicant Portal</span>
              </button>
            </div>
          </div>
        </div>

        {/* Offline Guarantee Footer */}
        <div className="mt-6 text-center">
          <p className="text-[11px] text-slate-500 leading-relaxed">
            <Lock className="w-3 h-3 inline mr-1 text-emerald-400" />
            {t('auth.offlineNotice')}
          </p>
        </div>
      </div>
    </div>
  );
};
