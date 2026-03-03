'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import type { AdminStats, SessionInfo, WebinarSettings } from '@/types';

const ID_REGEX = /^\d{8}$/;

type TabType = 'overview' | 'its' | 'majlis' | 'sessions';

export default function AdminDashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [itsIds, setItsIds] = useState<string[]>([]);
  const [majlisIds, setMajlisIds] = useState<string[]>([]);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [itsSettings, setItsSettings] = useState<WebinarSettings | null>(null);
  const [majlisSettings, setMajlisSettings] = useState<WebinarSettings | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Form states
  const [newItsId, setNewItsId] = useState('');
  const [bulkItsIds, setBulkItsIds] = useState('');
  const [newMajlisId, setNewMajlisId] = useState('');
  const [bulkMajlisIds, setBulkMajlisIds] = useState('');

  // Search/filter states
  const [itsSearchTerm, setItsSearchTerm] = useState('');
  const [majlisSearchTerm, setMajlisSearchTerm] = useState('');
  const [sessionFilterType, setSessionFilterType] = useState<'all' | 'its' | 'majlis'>('all');

  const showMessage = useCallback((type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, itsRes, majlisRes, sessionsRes, itsSettingsRes, majlisSettingsRes] = await Promise.all([
        fetch('/api/admin/sessions?action=stats'),
        fetch('/api/admin/its'),
        fetch('/api/admin/majlis'),
        fetch('/api/admin/sessions'),
        fetch('/api/admin/webinar-settings'),
        fetch('/api/admin/majlis-settings'),
      ]);

      const [statsData, itsData, majlisData, sessionsData, itsSettingsData, majlisSettingsData] = await Promise.all([
        statsRes.json(),
        itsRes.json(),
        majlisRes.json(),
        sessionsRes.json(),
        itsSettingsRes.json(),
        majlisSettingsRes.json(),
      ]);

      setStats(statsData);
      setItsIds(itsData.ids || []);
      setMajlisIds(majlisData.ids || []);
      setSessions(sessionsData.sessions || []);
      setItsSettings(itsSettingsData);
      setMajlisSettings(majlisSettingsData);
    } catch (e) {
      console.error('Failed to fetch data:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchData();

    // Connect to Server-Sent Events for real-time updates
    const eventSource = new EventSource('/api/admin/events');

    eventSource.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data);

        console.log('SSE Event received:', type, data);

        switch (type) {
          case 'connected':
            console.log('✅ Real-time updates connected');
            showMessage('success', 'Live updates connected');
            break;

          case 'user_connected':
            console.log('👤 User connected:', data);
            showMessage('info', `User ${data.user_id} connected (${data.user_type})`);
            fetchData();
            break;

          case 'user_disconnected':
            console.log('👋 User disconnected:', data);
            showMessage('info', `User ${data.user_id} disconnected (${data.user_type})`);
            fetchData();
            break;

          case 'ids_updated':
            console.log('📝 IDs updated:', data);
            fetchData();
            break;

          case 'settings_updated':
            console.log('⚙️ Settings updated:', data);
            fetchData();
            break;
        }
      } catch (error) {
        console.error('SSE parse error:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
    };

    eventSource.onopen = () => {
      console.log('SSE connection opened');
    };

    return () => {
      console.log('Closing SSE connection');
      eventSource.close();
    };
  }, [fetchData, showMessage]);

  const handleLogout = async () => {
    await fetch('/api/admin/logout', { method: 'POST' });
    router.push('/admin/login');
  };

  // --- ITS ID Management ---
  const addItsId = async () => {
    if (!ID_REGEX.test(newItsId)) {
      showMessage('error', 'Please enter a valid 8-digit ID');
      return;
    }
    const res = await fetch('/api/admin/its', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'add', id: newItsId }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `Asbaaq ID ${newItsId} added successfully`);
      setNewItsId('');
      fetchData();
    } else {
      showMessage('error', data.error || 'Failed to add ID');
    }
  };

  const addBulkItsIds = async () => {
    if (!bulkItsIds.trim()) {
      showMessage('error', 'Please enter IDs to add');
      return;
    }
    const res = await fetch('/api/admin/its', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'bulk_add', ids: bulkItsIds }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `Added ${data.count} Asbaaq ID(s)`);
      setBulkItsIds('');
      fetchData();
    } else {
      showMessage('error', data.error || 'Failed to add IDs');
    }
  };

  const deleteItsId = async (id: string) => {
    if (!confirm(`Delete Asbaaq ID ${id}?`)) return;
    const res = await fetch('/api/admin/its', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `Asbaaq ID ${id} deleted`);
      fetchData();
    } else {
      showMessage('error', data.error || 'Failed to delete ID');
    }
  };

  const deleteAllItsIds = async () => {
    if (!confirm('⚠️ Delete ALL Asbaaq IDs? This cannot be undone!')) return;
    const res = await fetch('/api/admin/its', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete_all' }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', 'All Asbaaq IDs deleted');
      fetchData();
    }
  };

  // --- Majlis ID Management ---
  const addMajlisId = async () => {
    if (!ID_REGEX.test(newMajlisId)) {
      showMessage('error', 'Please enter a valid 8-digit ID');
      return;
    }
    const res = await fetch('/api/admin/majlis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'add', id: newMajlisId }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `Majlis ID ${newMajlisId} added successfully`);
      setNewMajlisId('');
      fetchData();
    } else {
      showMessage('error', data.error || 'Failed to add ID');
    }
  };

  const addBulkMajlisIds = async () => {
    if (!bulkMajlisIds.trim()) {
      showMessage('error', 'Please enter IDs to add');
      return;
    }
    const res = await fetch('/api/admin/majlis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'bulk_add', ids: bulkMajlisIds }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `Added ${data.count} Majlis ID(s)`);
      setBulkMajlisIds('');
      fetchData();
    } else {
      showMessage('error', data.error || 'Failed to add IDs');
    }
  };

  const deleteMajlisId = async (id: string) => {
    if (!confirm(`Delete Majlis ID ${id}?`)) return;
    const res = await fetch('/api/admin/majlis', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `Majlis ID ${id} deleted`);
      fetchData();
    } else {
      showMessage('error', data.error || 'Failed to delete ID');
    }
  };

  const deleteAllMajlisIds = async () => {
    if (!confirm('⚠️ Delete ALL Majlis IDs? This cannot be undone!')) return;
    const res = await fetch('/api/admin/majlis', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete_all' }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', 'All Majlis IDs deleted');
      fetchData();
    }
  };

  // --- Webinar Settings ---
  const updateWebinarSettings = async (type: 'its' | 'majlis', formData: Record<string, string | boolean>) => {
    const endpoint = type === 'its' ? '/api/admin/webinar-settings' : '/api/admin/majlis-settings';
    const res = await fetch(endpoint, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `${type === 'its' ? 'Asbaaq' : 'Majlis'} webinar settings updated`);
      fetchData();
    } else {
      showMessage('error', data.error || 'Failed to update settings');
    }
  };

  // --- Session Management ---
  const kickSession = async (token: string) => {
    const res = await fetch('/api/admin/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'kick', token }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', 'Session kicked');
      fetchData();
    }
  };

  const forceLogoutUser = async (userId: string, userType: string) => {
    if (!confirm(`Force logout all sessions for user ${userId}?`)) return;
    const res = await fetch('/api/admin/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'force_logout', user_id: userId, user_type: userType }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', `Force logged out user ${userId}`);
      fetchData();
    }
  };

  const clearAllSessions = async () => {
    if (!confirm('⚠️ Clear ALL active sessions? All users will be logged out!')) return;
    const res = await fetch('/api/admin/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'clear_all' }),
    });
    const data = await res.json();
    if (data.success) {
      showMessage('success', 'All sessions cleared');
      fetchData();
    }
  };


  // Filtered data
  const filteredItsIds = itsIds.filter(id => id.includes(itsSearchTerm));
  const filteredMajlisIds = majlisIds.filter(id => id.includes(majlisSearchTerm));
  const filteredSessions = sessions.filter(s =>
    sessionFilterType === 'all' || s.user_type === sessionFilterType
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-dark)' }}>
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 border-4 border-accent-gold/20 border-t-accent-gold rounded-full animate-spin" />
          <p className="text-white/50 text-sm">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #090d1b 0%, #0f1428 50%, #090d1b 100%)' }}>
      {/* Modern Header with Gradient */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-surface-dark/80 border-b border-accent-gold/20 shadow-lg">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Image
                src="https://i.ibb.co/nqfBrMmC/logo-without-back.png"
                alt="Logo"
                width={48}
                height={48}
                className="rounded-xl shadow-lg"
              />
              <div>
                <h1 className="font-display text-2xl font-bold gradient-text">Admin Control Center</h1>
                <p className="text-white/40 text-xs">Webinar Management Portal</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/30">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-green-400 text-xs font-medium">Live Updates</span>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 transition-all text-sm"
              >
                <i aria-hidden="true" className="fas fa-sign-out-alt mr-2" />
                Logout
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex gap-2 mt-6 overflow-x-auto pb-1">
            {[
              { key: 'overview' as TabType, label: 'Dashboard', icon: 'fas fa-chart-line' },
              { key: 'its' as TabType, label: 'Asbaaq', icon: 'fas fa-mosque' },
              { key: 'majlis' as TabType, label: 'Majlis', icon: 'fas fa-users' },
              { key: 'sessions' as TabType, label: 'Active Sessions', icon: 'fas fa-signal' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`
                  px-6 py-3 rounded-lg font-semibold text-sm whitespace-nowrap transition-all
                  ${activeTab === tab.key
                    ? 'bg-gradient-to-r from-brand-primary to-brand-primary-light text-white shadow-brand'
                    : 'bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/70'
                  }
                `}
              >
                <i aria-hidden="true" className={`${tab.icon} mr-2`} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Flash Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg border animate-slide-in ${
            message.type === 'success'
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : message.type === 'info'
              ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            <i aria-hidden="true" className={`fas ${message.type === 'success' ? 'fa-check-circle' : message.type === 'info' ? 'fa-info-circle' : 'fa-exclamation-circle'} mr-2`} />
            {message.text}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'overview' && <OverviewTab stats={stats} sessions={sessions} onClearSessions={clearAllSessions} />}
        {activeTab === 'its' && (
          <ItsManagementTab
            ids={filteredItsIds}
            allIds={itsIds}
            settings={itsSettings}
            newId={newItsId}
            setNewId={setNewItsId}
            bulkIds={bulkItsIds}
            setBulkIds={setBulkItsIds}
            searchTerm={itsSearchTerm}
            setSearchTerm={setItsSearchTerm}
            onAddId={addItsId}
            onAddBulk={addBulkItsIds}
            onDeleteId={deleteItsId}
            onDeleteAll={deleteAllItsIds}
            onUpdateSettings={(formData) => updateWebinarSettings('its', formData)}
          />
        )}
        {activeTab === 'majlis' && (
          <MajlisManagementTab
            ids={filteredMajlisIds}
            allIds={majlisIds}
            settings={majlisSettings}
            newId={newMajlisId}
            setNewId={setNewMajlisId}
            bulkIds={bulkMajlisIds}
            setBulkIds={setBulkMajlisIds}
            searchTerm={majlisSearchTerm}
            setSearchTerm={setMajlisSearchTerm}
            onAddId={addMajlisId}
            onAddBulk={addBulkMajlisIds}
            onDeleteId={deleteMajlisId}
            onDeleteAll={deleteAllMajlisIds}
            onUpdateSettings={(formData) => updateWebinarSettings('majlis', formData)}
          />
        )}
        {activeTab === 'sessions' && (
          <SessionsTab
            sessions={filteredSessions}
            allSessions={sessions}
            filterType={sessionFilterType}
            setFilterType={setSessionFilterType}
            onKick={kickSession}
            onForceLogout={forceLogoutUser}
            onClearAll={clearAllSessions}
          />
        )}
      </div>
    </div>
  );
}

// ============ SUB-COMPONENTS ============

interface OverviewTabProps {
  stats: AdminStats | null;
  sessions: SessionInfo[];
  onClearSessions: () => void;
}

function OverviewTab({ stats, sessions, onClearSessions }: OverviewTabProps) {
  const recentSessions = sessions.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon="fas fa-id-card"
          label="Total Asbaaq IDs"
          value={stats?.total_its || 0}
          color="blue"
        />
        <StatCard
          icon="fas fa-id-card"
          label="Total Majlis IDs"
          value={stats?.total_majlis || 0}
          color="purple"
        />
        <StatCard
          icon="fas fa-signal"
          label="Asbaaq Sessions"
          value={stats?.its_sessions || 0}
          color="green"
        />
        <StatCard
          icon="fas fa-signal"
          label="Majlis Sessions"
          value={stats?.majlis_sessions || 0}
          color="orange"
        />
        <StatCard
          icon="fas fa-users"
          label="Total Active"
          value={stats?.total_sessions || 0}
          color="gold"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickActionCard
          icon="fas fa-play-circle"
          title="Asbaaq Webinar"
          description="Manage Asbaaq webinar stream settings"
          href="#"
          onClick={() => {}}
        />
        <QuickActionCard
          icon="fas fa-video"
          title="Majlis Webinar"
          description="Manage Majlis webinar stream settings"
          href="#"
          onClick={() => {}}
        />
        <QuickActionCard
          icon="fas fa-trash-alt"
          title="Clear All Sessions"
          description="Force logout all active users"
          href="#"
          onClick={onClearSessions}
          danger
        />
      </div>

      {/* Recent Activity */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <i className="fas fa-clock text-accent-gold" />
            Recent Sessions
          </h2>
          <span className="text-sm text-white/40">{sessions.length} total</span>
        </div>

        {recentSessions.length === 0 ? (
          <p className="text-white/30 text-center py-8">No active sessions</p>
        ) : (
          <div className="space-y-3">
            {recentSessions.map((s) => (
              <div key={s.token} className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${s.user_type === 'its' ? 'bg-blue-400' : 'bg-purple-400'}`} />
                  <span className="font-mono text-white/80">{s.user_id}</span>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    s.user_type === 'its' ? 'bg-blue-500/20 text-blue-300' : 'bg-purple-500/20 text-purple-300'
                  }`}>
                    {s.user_type === 'its' ? 'Asbaaq' : 'Majlis'}
                  </span>
                </div>
                <span className="text-xs text-white/40">
                  {new Date(s.login_time).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: string;
  label: string;
  value: number;
  color: 'blue' | 'purple' | 'green' | 'orange' | 'gold';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/20 border-blue-500/30 text-blue-400',
    purple: 'from-purple-500/20 to-purple-600/20 border-purple-500/30 text-purple-400',
    green: 'from-green-500/20 to-green-600/20 border-green-500/30 text-green-400',
    orange: 'from-orange-500/20 to-orange-600/20 border-orange-500/30 text-orange-400',
    gold: 'from-accent-gold/20 to-accent-gold-light/20 border-accent-gold/30 text-accent-gold',
  };

  return (
    <div className={`rounded-xl p-6 border bg-gradient-to-br ${colorClasses[color]} transition-all hover:scale-105`}>
      <div className="flex items-center justify-between mb-3">
        <i className={`${icon} text-2xl`} />
      </div>
      <div className="text-3xl font-bold mb-1">{value.toLocaleString()}</div>
      <div className="text-xs opacity-80">{label}</div>
    </div>
  );
}

interface QuickActionCardProps {
  icon: string;
  title: string;
  description: string;
  href: string;
  onClick: () => void;
  danger?: boolean;
}

function QuickActionCard({ icon, title, description, onClick, danger }: QuickActionCardProps) {
  return (
    <button
      onClick={onClick}
      className={`
        text-left p-6 rounded-xl border transition-all hover:scale-[1.02]
        ${danger
          ? 'bg-red-500/10 border-red-500/30 hover:bg-red-500/20'
          : 'glass hover:border-accent-gold/40'
        }
      `}
    >
      <i className={`${icon} text-3xl mb-3 ${danger ? 'text-red-400' : 'text-accent-gold'}`} />
      <h3 className={`text-lg font-semibold mb-1 ${danger ? 'text-red-300' : 'text-white'}`}>{title}</h3>
      <p className="text-sm text-white/50">{description}</p>
    </button>
  );
}

interface ItsManagementTabProps {
  ids: string[];
  allIds: string[];
  settings: WebinarSettings | null;
  newId: string;
  setNewId: (v: string) => void;
  bulkIds: string;
  setBulkIds: (v: string) => void;
  searchTerm: string;
  setSearchTerm: (v: string) => void;
  onAddId: () => void;
  onAddBulk: () => void;
  onDeleteId: (id: string) => void;
  onDeleteAll: () => void;
  onUpdateSettings: (data: Record<string, string | boolean>) => void;
}

function ItsManagementTab(props: ItsManagementTabProps) {
  const { ids, allIds, settings, newId, setNewId, bulkIds, setBulkIds, searchTerm, setSearchTerm, onAddId, onAddBulk, onDeleteId, onDeleteAll, onUpdateSettings } = props;

  const [videoId, setVideoId] = useState(settings?.youtube_video_id || '');
  const [title, setTitle] = useState(settings?.webinar_title || '');
  const [noWebinar, setNoWebinar] = useState(settings?.no_webinar || false);

  useEffect(() => {
    if (settings) {
      setVideoId(settings.youtube_video_id);
      setTitle(settings.webinar_title);
      setNoWebinar(settings.no_webinar);
    }
  }, [settings]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column - ID Management */}
      <div className="lg:col-span-2 space-y-6">
        {/* Add IDs Section */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <i className="fas fa-plus-circle text-accent-gold" />
            Add Asbaaq IDs
          </h2>

          <div className="space-y-4">
            {/* Single Add */}
            <div>
              <label className="block text-white/60 text-sm mb-2 font-medium">Add Single ID</label>
              <div className="flex gap-3">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={8}
                  value={newId}
                  onChange={(e) => setNewId(e.target.value.replace(/\D/g, '').slice(0, 8))}
                  placeholder="Enter 8-digit Asbaaq ID"
                  className="input-field flex-1 font-mono"
                />
                <button onClick={onAddId} className="btn-brand whitespace-nowrap px-6">
                  <i className="fas fa-plus mr-2" />
                  Add
                </button>
              </div>
            </div>

            {/* Bulk Add */}
            <div>
              <label className="block text-white/60 text-sm mb-2 font-medium">Bulk Add (comma or newline separated)</label>
              <textarea
                value={bulkIds}
                onChange={(e) => setBulkIds(e.target.value)}
                placeholder="12345678, 87654321&#10;11223344"
                className="input-field min-h-[120px] resize-y font-mono text-sm"
                rows={4}
              />
              <button onClick={onAddBulk} className="btn-brand mt-3">
                <i className="fas fa-upload mr-2" />
                Bulk Add
              </button>
            </div>
          </div>
        </div>

        {/* ID List */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <i className="fas fa-list text-accent-gold" />
              Asbaaq IDs ({allIds.length})
            </h2>
            {allIds.length > 0 && (
              <button onClick={onDeleteAll} className="btn-danger text-sm">
                <i className="fas fa-trash mr-2" />
                Delete All
              </button>
            )}
          </div>

          {/* Search */}
          <div className="mb-4">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search IDs..."
              className="input-field w-full"
            />
          </div>

          {/* List */}
          <div className="max-h-[500px] overflow-y-auto space-y-2">
            {ids.length === 0 ? (
              <p className="text-white/30 text-center py-8">
                {searchTerm ? 'No matching IDs' : 'No IDs registered'}
              </p>
            ) : (
              ids.map((id) => (
                <div key={id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group">
                  <span className="font-mono text-white/80 text-sm">{id}</span>
                  <button
                    onClick={() => onDeleteId(id)}
                    className="opacity-0 group-hover:opacity-100 text-red-400/60 hover:text-red-400 transition-all text-sm"
                  >
                    <i className="fas fa-trash-alt" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Right Column - Webinar Settings */}
      <div className="space-y-6">
        <WebinarSettingsPanel
          type="Asbaaq"
          videoId={videoId}
          setVideoId={setVideoId}
          title={title}
          setTitle={setTitle}
          noWebinar={noWebinar}
          setNoWebinar={setNoWebinar}
          onSave={() => onUpdateSettings({
            youtube_video_id: videoId,
            webinar_title: title,
            no_webinar: noWebinar,
          })}
        />
      </div>
    </div>
  );
}

// Majlis tab is identical structure
interface MajlisManagementTabProps {
  ids: string[];
  allIds: string[];
  settings: WebinarSettings | null;
  newId: string;
  setNewId: (v: string) => void;
  bulkIds: string;
  setBulkIds: (v: string) => void;
  searchTerm: string;
  setSearchTerm: (v: string) => void;
  onAddId: () => void;
  onAddBulk: () => void;
  onDeleteId: (id: string) => void;
  onDeleteAll: () => void;
  onUpdateSettings: (data: Record<string, string | boolean>) => void;
}

function MajlisManagementTab(props: MajlisManagementTabProps) {
  const { ids, allIds, settings, newId, setNewId, bulkIds, setBulkIds, searchTerm, setSearchTerm, onAddId, onAddBulk, onDeleteId, onDeleteAll, onUpdateSettings } = props;

  const [videoId, setVideoId] = useState(settings?.youtube_video_id || '');
  const [title, setTitle] = useState(settings?.webinar_title || '');
  const [noWebinar, setNoWebinar] = useState(settings?.no_webinar || false);

  useEffect(() => {
    if (settings) {
      setVideoId(settings.youtube_video_id);
      setTitle(settings.webinar_title);
      setNoWebinar(settings.no_webinar);
    }
  }, [settings]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Same structure as ITS but with "Majlis" labels */}
      <div className="lg:col-span-2 space-y-6">
        <div className="glass rounded-2xl p-6">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <i className="fas fa-plus-circle text-accent-gold" />
            Add Majlis IDs
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-white/60 text-sm mb-2 font-medium">Add Single ID</label>
              <div className="flex gap-3">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={8}
                  value={newId}
                  onChange={(e) => setNewId(e.target.value.replace(/\D/g, '').slice(0, 8))}
                  placeholder="Enter 8-digit Majlis ID"
                  className="input-field flex-1 font-mono"
                />
                <button onClick={onAddId} className="btn-brand whitespace-nowrap px-6">
                  <i className="fas fa-plus mr-2" />
                  Add
                </button>
              </div>
            </div>

            <div>
              <label className="block text-white/60 text-sm mb-2 font-medium">Bulk Add (comma or newline separated)</label>
              <textarea
                value={bulkIds}
                onChange={(e) => setBulkIds(e.target.value)}
                placeholder="12345678, 87654321&#10;11223344"
                className="input-field min-h-[120px] resize-y font-mono text-sm"
                rows={4}
              />
              <button onClick={onAddBulk} className="btn-brand mt-3">
                <i className="fas fa-upload mr-2" />
                Bulk Add
              </button>
            </div>
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <i className="fas fa-list text-accent-gold" />
              Majlis IDs ({allIds.length})
            </h2>
            {allIds.length > 0 && (
              <button onClick={onDeleteAll} className="btn-danger text-sm">
                <i className="fas fa-trash mr-2" />
                Delete All
              </button>
            )}
          </div>

          <div className="mb-4">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search IDs..."
              className="input-field w-full"
            />
          </div>

          <div className="max-h-[500px] overflow-y-auto space-y-2">
            {ids.length === 0 ? (
              <p className="text-white/30 text-center py-8">
                {searchTerm ? 'No matching IDs' : 'No IDs registered'}
              </p>
            ) : (
              ids.map((id) => (
                <div key={id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group">
                  <span className="font-mono text-white/80 text-sm">{id}</span>
                  <button
                    onClick={() => onDeleteId(id)}
                    className="opacity-0 group-hover:opacity-100 text-red-400/60 hover:text-red-400 transition-all text-sm"
                  >
                    <i className="fas fa-trash-alt" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <WebinarSettingsPanel
          type="Majlis"
          videoId={videoId}
          setVideoId={setVideoId}
          title={title}
          setTitle={setTitle}
          noWebinar={noWebinar}
          setNoWebinar={setNoWebinar}
          onSave={() => onUpdateSettings({
            youtube_video_id: videoId,
            webinar_title: title,
            no_webinar: noWebinar,
          })}
        />
      </div>
    </div>
  );
}

interface WebinarSettingsPanelProps {
  type: string;
  videoId: string;
  setVideoId: (v: string) => void;
  title: string;
  setTitle: (v: string) => void;
  noWebinar: boolean;
  setNoWebinar: (v: boolean) => void;
  onSave: () => void;
}

function WebinarSettingsPanel(props: WebinarSettingsPanelProps) {
  const { type, videoId, setVideoId, title, setTitle, noWebinar, setNoWebinar, onSave } = props;

  return (
    <div className="glass rounded-2xl p-6 sticky top-24">
      <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <i className="fas fa-cog text-accent-gold" />
        {type} Webinar Settings
      </h2>

      <div className="space-y-4">
        <div>
          <label className="block text-white/60 text-xs mb-2 font-medium">YouTube Video ID / URL</label>
          <input
            type="text"
            value={videoId}
            onChange={(e) => setVideoId(e.target.value)}
            placeholder="e.g. dQw4w9WgXcQ"
            className="input-field text-sm"
          />
        </div>

        <div>
          <label className="block text-white/60 text-xs mb-2 font-medium">Webinar Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input-field text-sm"
          />
        </div>

        <div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={noWebinar}
              onChange={(e) => setNoWebinar(e.target.checked)}
            />
            <span className="text-sm">No Webinar (Disable Stream)</span>
          </label>
        </div>

        <button onClick={onSave} className="w-full btn-gold py-3">
          <i className="fas fa-save mr-2" />
          Save Settings
        </button>
      </div>
    </div>
  );
}

interface SessionsTabProps {
  sessions: SessionInfo[];
  allSessions: SessionInfo[];
  filterType: 'all' | 'its' | 'majlis';
  setFilterType: (v: 'all' | 'its' | 'majlis') => void;
  onKick: (token: string) => void;
  onForceLogout: (userId: string, userType: string) => void;
  onClearAll: () => void;
}

function SessionsTab({ sessions, allSessions, filterType, setFilterType, onKick, onForceLogout, onClearAll }: SessionsTabProps) {
  const itsCount = allSessions.filter(s => s.user_type === 'its').length;
  const majlisCount = allSessions.filter(s => s.user_type === 'majlis').length;

  return (
    <div className="space-y-6">
      {/* Filter Tabs */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <i className="fas fa-signal text-accent-gold" />
            Active Sessions
          </h2>
          <button onClick={onClearAll} className="btn-danger text-sm">
            <i className="fas fa-trash-alt mr-2" />
            Clear All Sessions
          </button>
        </div>

        <div className="flex gap-2 mb-6">
          {[
            { key: 'all' as const, label: 'All', count: allSessions.length },
            { key: 'its' as const, label: 'Asbaaq', count: itsCount },
            { key: 'majlis' as const, label: 'Majlis', count: majlisCount },
          ].map((filter) => (
            <button
              key={filter.key}
              onClick={() => setFilterType(filter.key)}
              className={`
                px-6 py-2 rounded-lg font-semibold text-sm transition-all
                ${filterType === filter.key
                  ? 'bg-accent-gold text-black'
                  : 'bg-white/5 text-white/50 hover:bg-white/10'
                }
              `}
            >
              {filter.label} ({filter.count})
            </button>
          ))}
        </div>

        {/* Session Table */}
        {sessions.length === 0 ? (
          <p className="text-white/30 text-center py-12">No active sessions</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-3 px-4 text-white/60 text-xs font-semibold uppercase">User ID</th>
                  <th className="text-left py-3 px-4 text-white/60 text-xs font-semibold uppercase">Type</th>
                  <th className="text-left py-3 px-4 text-white/60 text-xs font-semibold uppercase">Login Time</th>
                  <th className="text-left py-3 px-4 text-white/60 text-xs font-semibold uppercase">Last Activity</th>
                  <th className="text-right py-3 px-4 text-white/60 text-xs font-semibold uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.token} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-3 px-4 font-mono text-white/80 text-sm">{s.user_id}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        s.user_type === 'its' ? 'bg-blue-500/20 text-blue-300' : 'bg-purple-500/20 text-purple-300'
                      }`}>
                        {s.user_type === 'its' ? 'Asbaaq' : 'Majlis'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-white/60 text-sm">{new Date(s.login_time).toLocaleString()}</td>
                    <td className="py-3 px-4 text-white/60 text-sm">{new Date(s.last_activity).toLocaleString()}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => onKick(s.token)}
                          className="px-3 py-1 rounded bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 text-xs transition-colors"
                        >
                          <i className="fas fa-sign-out-alt mr-1" />
                          Kick
                        </button>
                        <button
                          onClick={() => onForceLogout(s.user_id, s.user_type)}
                          className="px-3 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs transition-colors"
                        >
                          <i className="fas fa-power-off mr-1" />
                          Force
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
