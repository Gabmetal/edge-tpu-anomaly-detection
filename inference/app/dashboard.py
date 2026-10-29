"""
dashboard.py
Embedded Cyber SOC Dashboard for Edge TPU Anomaly Detection Microservice.
Served directly as modern responsive single-page application at '/' and '/ui'.
Includes:
  - Mobile-first responsive navigation with drawer
  - Live hardware HUD & sub-millisecond Coral TPU meters
  - Real-time Chart.js MSE streaming chart & feature residuals
  - Interactive attack simulator testbench
  - Live Flagged Incidents & Quarantine Audit Log table
  - Direct portals to AdGuard Home Query Log, OpenWrt Firewall, and Grafana
"""

def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en" class="dark scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>Edge TPU Anomaly Detection SOC</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2306b6d4'><circle cx='12' cy='12' r='10'/></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="/static/chart.umd.min.js"></script>
  <script>
    if (typeof Chart === 'undefined') {
      document.write('<script src="https://cdn.jsdelivr.net/npm/chart.js"><\\/script>');
    }
  </script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#ecfeff',
              400: '#22d3ee',
              500: '#06b6d4',
              600: '#0891b2',
              900: '#164e63',
            },
            surface: {
              700: '#334155',
              800: '#1e293b',
              850: '#172033',
              900: '#0f172a',
              950: '#020617'
            }
          }
        }
      }
    }
  </script>
  <style>
    @keyframes pulse-subtle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
    .animate-pulse-subtle {
      animation: pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    @keyframes spin-reverse {
      from { transform: rotate(0deg); }
      to { transform: rotate(-360deg); }
    }
    .animate-spin-reverse {
      animation: spin-reverse 3s linear infinite;
    }
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: #020617;
    }
    ::-webkit-scrollbar-thumb {
      background: #334155;
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #475569;
    }
  </style>
</head>
<body class="bg-surface-950 text-slate-100 font-sans min-h-screen flex flex-col antialiased selection:bg-brand-500 selection:text-white">

  <!-- Top Sticky Navigation Bar -->
  <header class="border-b border-slate-800/80 bg-surface-950/85 backdrop-blur-md sticky top-0 z-50 transition-all duration-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        
        <!-- Left: Logo & Branding -->
        <div class="flex items-center space-x-3 min-w-0">
          <a href="#" class="flex items-center space-x-3 group">
            <div class="h-9 w-9 rounded-lg bg-gradient-to-tr from-brand-600 via-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20 group-hover:scale-105 transition-transform shrink-0">
              <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div class="truncate">
              <div class="flex items-center space-x-2">
                <span class="text-sm sm:text-base font-bold tracking-tight text-white group-hover:text-brand-400 transition-colors">Edge TPU SOC</span>
                <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 shrink-0" id="tpu-pill">
                  <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
                  <span class="hidden xs:inline">Coral </span>Active
                </span>
              </div>
              <p class="hidden sm:block text-[11px] text-slate-400 truncate">K3s Bare-Metal &bull; Sub-ms INT8 Neural Defense</p>
            </div>
          </a>
        </div>

        <!-- Center: Desktop Navigation Anchor Links -->
        <nav class="hidden xl:flex items-center space-x-1 bg-surface-900/60 p-1 rounded-xl border border-slate-800/80 text-xs font-medium text-slate-300">
          <a href="#overview" class="px-3 py-1.5 rounded-lg hover:text-white hover:bg-surface-800 transition">Overview</a>
          <a href="#metrics" class="px-3 py-1.5 rounded-lg hover:text-white hover:bg-surface-800 transition">Live MSE</a>
          <a href="#simulator" class="px-3 py-1.5 rounded-lg hover:text-white hover:bg-surface-800 transition">Simulator</a>
          <a href="#events" class="px-3 py-1.5 rounded-lg hover:text-white hover:bg-surface-800 transition text-brand-400 font-semibold flex items-center space-x-1">
            <span>Flagged Events</span>
            <span class="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse"></span>
          </a>
          <a href="#infrastructure" class="px-3 py-1.5 rounded-lg hover:text-white hover:bg-surface-800 transition">Topology</a>
        </nav>

        <!-- Right: Telemetry Badges & Action Buttons -->
        <div class="flex items-center space-x-2 sm:space-x-3">
          
          <!-- Live Telemetry Stats (Desktop / Tablet) -->
          <div class="hidden md:flex items-center space-x-2 text-xs">
            <div class="flex items-center space-x-1.5 bg-surface-900 px-2.5 py-1.5 rounded-lg border border-slate-800">
              <span class="text-slate-400 text-[11px]">Threshold:</span>
              <span class="font-mono text-brand-400 font-semibold text-[11px]" id="top-threshold">0.001806</span>
            </div>
            <div class="flex items-center space-x-1.5 bg-surface-900 px-2.5 py-1.5 rounded-lg border border-slate-800">
              <span class="text-slate-400 text-[11px]">Latency:</span>
              <span class="font-mono text-emerald-400 font-bold text-[11px]" id="top-latency">0.38 ms</span>
            </div>
          </div>

          <!-- Live Refresh / Polling Button -->
          <button id="poll-toggle-btn" onclick="togglePolling()" title="Pause or Resume Live Polling" class="p-2 rounded-lg bg-surface-900 hover:bg-surface-800 border border-slate-800 text-slate-300 hover:text-white transition">
            <svg id="poll-icon" class="h-4 w-4 text-emerald-400 animate-spin-reverse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>

          <!-- External Links -->
          <div class="hidden sm:flex items-center space-x-1.5 text-xs">
            <a href="/docs" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-surface-900 hover:bg-surface-800 border border-slate-800 text-slate-300 hover:text-white transition">API Docs</a>
            <a href="https://grafana.gabo.lat" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-indigo-950/60 hover:bg-indigo-900/80 border border-indigo-800/60 text-indigo-300 hover:text-white transition flex items-center space-x-1">
              <span>Grafana</span>
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
            </a>
          </div>

          <!-- Mobile Hamburger Toggle Button -->
          <button type="button" onclick="toggleMobileMenu()" class="xl:hidden p-2 rounded-lg bg-surface-900 hover:bg-surface-800 border border-slate-800 text-slate-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-brand-500" aria-label="Toggle navigation">
            <svg id="hamburger-icon" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <svg id="close-icon" class="h-5 w-5 hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

        </div>

      </div>
    </div>

    <!-- Mobile Collapsible Menu Drawer -->
    <div id="mobile-menu" class="hidden xl:hidden border-b border-slate-800/80 bg-surface-900/95 backdrop-blur-xl px-4 pt-3 pb-5 space-y-3">
      
      <!-- Mobile Nav Links -->
      <nav class="grid grid-cols-2 gap-2 text-xs font-medium text-slate-300">
        <a href="#overview" onclick="toggleMobileMenu()" class="p-2.5 rounded-lg bg-surface-800 hover:bg-slate-700/80 flex items-center space-x-2">
          <svg class="h-4 w-4 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
          <span>Overview</span>
        </a>
        <a href="#metrics" onclick="toggleMobileMenu()" class="p-2.5 rounded-lg bg-surface-800 hover:bg-slate-700/80 flex items-center space-x-2">
          <svg class="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/></svg>
          <span>Live MSE</span>
        </a>
        <a href="#simulator" onclick="toggleMobileMenu()" class="p-2.5 rounded-lg bg-surface-800 hover:bg-slate-700/80 flex items-center space-x-2">
          <svg class="h-4 w-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
          <span>Simulator</span>
        </a>
        <a href="#events" onclick="toggleMobileMenu()" class="p-2.5 rounded-lg bg-surface-800 hover:bg-slate-700/80 flex items-center space-x-2 text-rose-300">
          <svg class="h-4 w-4 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          <span>Flagged Events</span>
        </a>
      </nav>

      <!-- Mobile Quick Stats Cards -->
      <div class="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-slate-800/80">
        <div class="bg-surface-950 p-2.5 rounded-lg border border-slate-800">
          <span class="text-slate-400 text-[10px] block">Threshold</span>
          <span class="font-mono text-brand-400 font-semibold text-xs" id="mob-threshold">0.001806</span>
        </div>
        <div class="bg-surface-950 p-2.5 rounded-lg border border-slate-800">
          <span class="text-slate-400 text-[10px] block">TPU Latency</span>
          <span class="font-mono text-emerald-400 font-bold text-xs" id="mob-latency">0.38 ms</span>
        </div>
      </div>

      <!-- Mobile Action Buttons -->
      <div class="flex items-center space-x-2 pt-1 text-xs">
        <a href="/docs" target="_blank" class="flex-1 text-center py-2 rounded-lg bg-surface-800 hover:bg-slate-700 border border-slate-700 text-slate-200">
          API Swagger
        </a>
        <a href="https://grafana.gabo.lat" target="_blank" class="flex-1 text-center py-2 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-800 text-indigo-200 flex items-center justify-center space-x-1">
          <span>Grafana</span>
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
        </a>
      </div>

    </div>
  </header>

  <!-- Main Body Content -->
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 sm:space-y-8">

    <!-- Anomaly Alert Banner (Conditional) -->
    <div id="alert-banner" class="hidden rounded-xl border border-rose-500/50 bg-rose-950/50 p-4 sm:p-5 backdrop-blur-md shadow-xl shadow-rose-950/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="flex items-start space-x-3 sm:space-x-4">
        <div class="h-10 w-10 sm:h-12 sm:w-12 rounded-xl bg-rose-500/20 border border-rose-500/50 flex items-center justify-center text-rose-400 shrink-0">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h3 class="text-sm sm:text-base font-bold text-rose-300 uppercase tracking-wide">Anomaly Threshold Breach</h3>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500 text-white uppercase animate-pulse">Critical</span>
          </div>
          <p class="text-xs text-rose-200/90 mt-1" id="alert-detail">Latest 10-second telemetry window yielded an autoencoder reconstruction loss significantly higher than normal baseline.</p>
        </div>
      </div>
      <div class="w-full sm:w-auto flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t sm:border-t-0 border-rose-900/50 pt-3 sm:pt-0">
        <span class="text-xs text-rose-300/80 sm:hidden">Loss Value:</span>
        <span class="px-3 py-1 rounded-lg bg-rose-500/30 text-rose-200 font-mono text-sm font-bold border border-rose-500/40" id="alert-mse-value">MSE: 0.0450</span>
      </div>
    </div>

    <!-- Section 1: Overview KPIs Grid -->
    <section id="overview" class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">System Telemetry & Acceleration</h2>
        <span class="text-[11px] text-slate-500 font-mono" id="last-updated-text">Updated just now</span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <!-- Card 1: Live MSE -->
        <div class="bg-surface-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Reconstruction Error</span>
            <span class="font-mono text-[10px] text-slate-500">MSE Loss</span>
          </div>
          <div class="mt-3 flex items-baseline space-x-2">
            <span class="text-2xl sm:text-3xl font-bold font-mono text-emerald-400 tracking-tight" id="card-mse">0.00052</span>
            <span class="text-xs text-slate-500 font-mono">/ <span id="card-threshold">0.00180</span></span>
          </div>
          <div class="mt-4 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div id="card-mse-bar" class="bg-emerald-400 h-full rounded-full transition-all duration-300" style="width: 28%"></div>
          </div>
          <div class="mt-2.5 text-[11px] text-slate-400 flex justify-between">
            <span>Status: <span id="card-status-text" class="text-emerald-400 font-medium">Nominal</span></span>
            <span id="card-status-percent" class="font-mono text-slate-500">28% of threshold</span>
          </div>
        </div>

        <!-- Card 2: TPU Latency -->
        <div class="bg-surface-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Hardware Execution</span>
            <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-brand-950 text-brand-400 border border-brand-800">SLA &lt; 2ms</span>
          </div>
          <div class="mt-3 flex items-baseline space-x-2">
            <span class="text-2xl sm:text-3xl font-bold font-mono text-brand-400 tracking-tight" id="card-latency">0.38</span>
            <span class="text-xs text-slate-400">ms / eval</span>
          </div>
          <div class="mt-4 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Core: <span class="text-slate-300 font-mono" id="card-device">Google Coral USB</span></span>
            <span class="text-emerald-400 font-mono text-[10px]">INT8 Systolic</span>
          </div>
        </div>

        <!-- Card 3: Inferences Count -->
        <div class="bg-surface-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Total Inferences</span>
            <span class="text-[10px] text-slate-500 font-mono">10s Windows</span>
          </div>
          <div class="mt-3 flex items-baseline space-x-2">
            <span class="text-2xl sm:text-3xl font-bold font-mono text-white tracking-tight" id="card-inferences">0</span>
            <span class="text-xs text-slate-400">evals</span>
          </div>
          <div class="mt-4 text-[11px] text-slate-400 flex justify-between">
            <span>Anomalies Flagged:</span>
            <span class="font-mono text-rose-400 font-bold" id="card-anomalies-count">0</span>
          </div>
        </div>

        <!-- Card 4: Ingress Pipeline -->
        <div class="bg-surface-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>Telemetry Ingress</span>
            <span class="flex items-center space-x-1">
              <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="text-[10px] text-emerald-400 font-mono">Vector VIP</span>
            </span>
          </div>
          <div class="mt-3 flex items-baseline space-x-2">
            <span class="text-xl sm:text-2xl font-bold font-mono text-slate-100">192.168.0.52</span>
          </div>
          <div class="mt-4 text-[11px] text-slate-400 flex justify-between">
            <span>Syslog UDP :514</span>
            <span>NetFlow UDP :2055</span>
          </div>
        </div>

      </div>
    </section>

    <!-- Section 2: Charts (Live MSE & Feature Residuals) -->
    <section id="metrics" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Neural Evaluation & Residual Breakdown</h2>
        <span class="text-[11px] text-slate-500 font-mono">Real-time Autoencoder Stream</span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Live MSE Rolling Window Chart -->
        <div class="lg:col-span-2 bg-surface-900 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-4">
            <div>
              <h3 class="text-sm font-bold text-white tracking-wide">Live Reconstruction Error (MSE)</h3>
              <p class="text-xs text-slate-400 mt-0.5">Continuous 10-second tumbling vector evaluation vs calibrated threshold</p>
            </div>
            <div class="flex items-center space-x-2 self-start sm:self-auto">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">3s Interval</span>
            </div>
          </div>
          <div class="h-60 sm:h-72 relative">
            <canvas id="mseChart"></canvas>
          </div>
        </div>

        <!-- 32-D Feature Residual Breakdown Chart -->
        <div class="bg-surface-900 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-sm font-bold text-white tracking-wide">Top Feature Residuals</h3>
                <p class="text-xs text-slate-400 mt-0.5">Root-cause contribution $(x_i - \\hat{x}_i)^2$</p>
              </div>
            </div>
            <div class="h-60 sm:h-72 relative">
              <canvas id="residualChart"></canvas>
            </div>
          </div>
          <p class="text-[10px] text-slate-500 text-center mt-2 font-mono">Top anomalous vector dimensions</p>
        </div>

      </div>
    </section>

    <!-- Section 3: Interactive Attack Simulator Workbench -->
    <section id="simulator" class="bg-surface-900 border border-slate-800 rounded-xl p-4 sm:p-6 shadow-sm space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-4">
        <div>
          <div class="flex items-center space-x-2">
            <h3 class="text-sm sm:text-base font-bold text-white tracking-wide">Interactive Attack Injection & Diagnostics</h3>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800">Testbench</span>
          </div>
          <p class="text-xs text-slate-400 mt-0.5">Inject synthetic network patterns directly into the Edge TPU neural inference loop to verify detection & mitigations</p>
        </div>
        <div class="text-xs text-slate-500 font-mono">
          Route: <code class="text-slate-300">POST /v1/predict</code>
        </div>
      </div>

      <!-- Action Buttons Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        
        <!-- Button 1: Normal Baseline -->
        <button onclick="injectScenario('normal')" class="p-3.5 bg-surface-850 hover:bg-slate-700/80 active:scale-[0.98] border border-slate-700 rounded-xl text-left transition flex flex-col justify-between group shadow-sm">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-emerald-400">Normal Baseline</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-emerald-950/80 border border-emerald-800 rounded text-emerald-300 font-medium">Clean</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-2 leading-relaxed">Typical flow rates, normal DNS resolution, nominal cluster traffic.</p>
          <span class="text-[11px] text-brand-400 font-mono mt-3 block group-hover:translate-x-0.5 transition-transform">&rarr; Inject Clean Vector</span>
        </button>

        <!-- Button 2: SYN Flood -->
        <button onclick="injectScenario('syn_flood')" class="p-3.5 bg-surface-850 hover:bg-rose-950/40 active:scale-[0.98] border border-rose-900/60 hover:border-rose-600 rounded-xl text-left transition flex flex-col justify-between group shadow-sm">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-rose-400">SYN Flood Surge</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-rose-950/80 border border-rose-800 rounded text-rose-300 font-medium">Attack</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-2 leading-relaxed">High pps, small packet sizes, 98% TCP SYN ratio anomaly.</p>
          <span class="text-[11px] text-rose-400 font-mono mt-3 block group-hover:translate-x-0.5 transition-transform">&rarr; Inject SYN Surge</span>
        </button>

        <!-- Button 3: DNS Tunnel -->
        <button onclick="injectScenario('dns_tunnel')" class="p-3.5 bg-surface-850 hover:bg-amber-950/40 active:scale-[0.98] border border-amber-900/60 hover:border-amber-600 rounded-xl text-left transition flex flex-col justify-between group shadow-sm">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-amber-400">DNS Tunneling</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-amber-950/80 border border-amber-800 rounded text-amber-300 font-medium">Attack</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-2 leading-relaxed">Surging NXDOMAIN rates, high entropy subdomains, DGA beaconing.</p>
          <span class="text-[11px] text-amber-400 font-mono mt-3 block group-hover:translate-x-0.5 transition-transform">&rarr; Inject Tunneling</span>
        </button>

        <!-- Button 4: Port Scan -->
        <button onclick="injectScenario('port_scan')" class="p-3.5 bg-surface-850 hover:bg-purple-950/40 active:scale-[0.98] border border-purple-900/60 hover:border-purple-600 rounded-xl text-left transition flex flex-col justify-between group shadow-sm">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-purple-400">Port Scan Sweep</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-purple-950/80 border border-purple-800 rounded text-purple-300 font-medium">Attack</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-2 leading-relaxed">High unique destination ports, elevated firewall reject rate.</p>
          <span class="text-[11px] text-purple-400 font-mono mt-3 block group-hover:translate-x-0.5 transition-transform">&rarr; Inject Sweep</span>
        </button>

      </div>

      <!-- Simulation Output Bar -->
      <div id="sim-result" class="hidden p-3.5 bg-surface-950 border border-slate-800 rounded-xl font-mono text-xs text-slate-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-inner">
        <span id="sim-text">Simulation dispatched</span>
        <span id="sim-latency" class="text-emerald-400 font-bold"></span>
      </div>
    </section>

    <!-- Section 4: Flagged Threat Incidents & Defense Audit Log -->
    <section id="events" class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <div class="flex items-center space-x-2">
            <h2 class="text-sm font-bold uppercase tracking-wider text-white">Flagged Threat Incidents & Defense Log</h2>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-950 text-rose-300 border border-rose-800/80">Real-Time Audit</span>
          </div>
          <p class="text-xs text-slate-400 mt-0.5">Chronological record of anomalous telemetry vectors evaluated on Edge TPU and router quarantine status</p>
        </div>
        
        <!-- Quick Portals to See Blocked Things -->
        <div class="flex items-center space-x-2 text-xs">
          <a href="https://adguard.gabo.lat/#logs" target="_blank" class="px-3 py-1.5 rounded-lg bg-surface-850 hover:bg-surface-800 border border-slate-700 text-slate-300 hover:text-white transition flex items-center space-x-1.5 shadow-sm">
            <span class="h-2 w-2 rounded-full bg-cyan-400"></span>
            <span>AdGuard Query Log</span>
            <svg class="h-3 w-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
          </a>
          <a href="https://192.168.0.1" target="_blank" class="px-3 py-1.5 rounded-lg bg-surface-850 hover:bg-surface-800 border border-slate-700 text-slate-300 hover:text-white transition flex items-center space-x-1.5 shadow-sm">
            <span class="h-2 w-2 rounded-full bg-emerald-400"></span>
            <span>OpenWrt Firewall</span>
            <svg class="h-3 w-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
          </a>
        </div>
      </div>

      <!-- Incidents Table Container -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-300 divide-y divide-slate-800/80">
            <thead class="bg-surface-950/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th scope="col" class="py-3 px-4">Status</th>
                <th scope="col" class="py-3 px-4">Timestamp</th>
                <th scope="col" class="py-3 px-4">Threat / Scenario</th>
                <th scope="col" class="py-3 px-4">Reconstruction MSE</th>
                <th scope="col" class="py-3 px-4">Root Cause Dimension</th>
                <th scope="col" class="py-3 px-4">Latency</th>
                <th scope="col" class="py-3 px-4">Mitigation Action</th>
              </tr>
            </thead>
            <tbody id="incidents-table-body" class="divide-y divide-slate-800/50 font-mono text-[11px]">
              <tr id="empty-table-row">
                <td colspan="7" class="py-8 text-center text-slate-500 font-sans text-xs">
                  <div class="flex flex-col items-center justify-center space-y-1">
                    <svg class="h-8 w-8 text-slate-600 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span>No critical anomalies flagged in recent window buffer.</span>
                    <span class="text-[11px] text-slate-600">Simulate an attack above or send live telemetry to populate incidents.</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Section 5: Nodes & Infrastructure Details -->
    <section id="infrastructure" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Cluster Nodes & Gateway Infrastructure</h2>
        <span class="text-[11px] text-slate-500 font-mono">Physical Topology</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        
        <!-- OpenWrt Node Info -->
        <div class="bg-surface-900 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-white flex items-center space-x-2">
              <span>OpenWrt Telemetry Gateway</span>
            </h3>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">192.168.0.1</span>
          </div>
          <dl class="divide-y divide-slate-800/80 text-xs">
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">Hardware & Release:</dt>
              <dd class="font-mono text-slate-200">OpenWrt 23.05.2 (MT7621 MIPS)</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">NetFlow Sniffer:</dt>
              <dd class="font-mono text-emerald-400">softflowd (NetFlow v9 &rarr; :2055)</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">Remote Syslog:</dt>
              <dd class="font-mono text-emerald-400">UDP :514 active</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">Automated Quarantine:</dt>
              <dd class="font-mono text-brand-400">inet fw4 quarantined_hosts</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">AdGuard Home DNS:</dt>
              <dd class="font-mono text-slate-300">
                <a href="https://adguard.gabo.lat/#logs" target="_blank" class="text-indigo-400 hover:underline">adguard.gabo.lat (Query Log) &rarr;</a>
              </dd>
            </div>
          </dl>
        </div>

        <!-- K3s Host Info -->
        <div class="bg-surface-900 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-white flex items-center space-x-2">
              <span>K3s Edge ML Hardware</span>
            </h3>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-brand-950 text-brand-400 border border-brand-800">xeon</span>
          </div>
          <dl class="divide-y divide-slate-800/80 text-xs">
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">Google Coral Accelerator:</dt>
              <dd class="font-mono text-emerald-400">/dev/bus/usb/003/003 (18d1:9302)</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">Runtime Delegate:</dt>
              <dd class="font-mono text-slate-200">libedgetpu.so.1 (Standard)</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">Model Topology:</dt>
              <dd class="font-mono text-slate-200">Dense(16) &rarr; Dense(8) &rarr; Dense(16) [INT8]</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">External Endpoint:</dt>
              <dd class="font-mono text-indigo-400">https://anomaly.gabo.lat</dd>
            </div>
            <div class="flex justify-between py-2">
              <dt class="text-slate-400">Authentication:</dt>
              <dd class="font-mono text-slate-300">Cloudflare Zero Trust Access</dd>
            </div>
          </dl>
        </div>

      </div>
    </section>

  </main>

  <!-- Sticky Bottom Quick-Jump on Mobile -->
  <div class="xl:hidden fixed bottom-4 right-4 z-40">
    <a href="#" class="h-10 w-10 rounded-full bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/30 flex items-center justify-center transition active:scale-90" aria-label="Back to top">
      <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
      </svg>
    </a>
  </div>

  <!-- Footer -->
  <footer class="border-t border-slate-800/80 bg-surface-950 text-center py-6 text-xs text-slate-500 px-4">
    <p>Edge ML Cyber Infrastructure &bull; Bare-Metal K3s &bull; Coral Edge TPU INT8 Acceleration</p>
    <p class="text-[11px] text-slate-600 mt-1">Protected by Cloudflare Access &bull; Vector Telemetry &bull; VictoriaMetrics</p>
  </footer>

  <!-- Dashboard JavaScript Logic -->
  <script>
    let currentThreshold = 0.045000;
    let totalInferences = 0;
    let anomaliesCount = 0;
    let isPolling = true;

    // Mobile Hamburger Menu Toggle
    function toggleMobileMenu() {
      const menu = document.getElementById('mobile-menu');
      const hamburger = document.getElementById('hamburger-icon');
      const close = document.getElementById('close-icon');
      if (menu.classList.contains('hidden')) {
        menu.classList.remove('hidden');
        hamburger.classList.add('hidden');
        close.classList.remove('hidden');
      } else {
        menu.classList.add('hidden');
        hamburger.classList.remove('hidden');
        close.classList.add('hidden');
      }
    }

    // Polling Toggle
    function togglePolling() {
      isPolling = !isPolling;
      const icon = document.getElementById('poll-icon');
      if (isPolling) {
        icon.classList.add('animate-spin-reverse');
        icon.classList.remove('text-slate-500');
        icon.classList.add('text-emerald-400');
        updateStatus();
        fetchEvents();
      } else {
        icon.classList.remove('animate-spin-reverse');
        icon.classList.remove('text-emerald-400');
        icon.classList.add('text-slate-500');
      }
    }

    // Chart.js: Safe Initialization
    let mseChart = null;
    let residualChart = null;

    try {
      const elMse = document.getElementById('mseChart');
      if (elMse && typeof Chart !== 'undefined') {
        const ctxMse = elMse.getContext('2d');
        const mseData = {
          labels: Array(20).fill(''),
          datasets: [
            {
              label: 'Reconstruction Loss (MSE)',
              data: Array(20).fill(0.0005),
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.12)',
              borderWidth: 2,
              fill: true,
              tension: 0.3,
              pointRadius: 2,
              pointHoverRadius: 4
            },
            {
              label: 'Anomaly Threshold',
              data: Array(20).fill(currentThreshold),
              borderColor: '#f43f5e',
              borderWidth: 1.5,
              borderDash: [5, 5],
              pointRadius: 0,
              fill: false
            }
          ]
        };
        mseChart = new Chart(ctxMse, {
          type: 'line',
          data: mseData,
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
              legend: { labels: { color: '#94a3b8', boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
              x: { grid: { color: 'rgba(51, 65, 85, 0.25)' }, ticks: { display: false } },
              y: {
                grid: { color: 'rgba(51, 65, 85, 0.25)' },
                ticks: { color: '#94a3b8', font: { family: 'monospace', size: 10 } },
                suggestedMin: 0,
                suggestedMax: 0.005
              }
            }
          }
        });
      }
    } catch (e) {
      console.warn('Failed to initialize mseChart', e);
    }

    try {
      const elRes = document.getElementById('residualChart');
      if (elRes && typeof Chart !== 'undefined') {
        const ctxResidual = elRes.getContext('2d');
        residualChart = new Chart(ctxResidual, {
          type: 'bar',
          data: {
            labels: ['tcp_ratio', 'syn_rate', 'fw_reject', 'dns_nx', 'k8s_err'],
            datasets: [{
              label: 'Residual Score',
              data: [0.008, 0.006, 0.004, 0.002, 0.001],
              backgroundColor: '#06b6d4',
              borderRadius: 4
            }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { color: 'rgba(51, 65, 85, 0.25)' }, ticks: { color: '#94a3b8', font: { size: 9 } } },
              y: { grid: { display: false }, ticks: { color: '#cbd5e1', font: { size: 10 } } }
            }
          }
        });
      }
    } catch (e) {
      console.warn('Failed to initialize residualChart', e);
    }

    // Render Event Rows in Flagged Events Table
    function renderEvents(events) {
      const tbody = document.getElementById('incidents-table-body');
      if (!events || events.length === 0) return;

      tbody.innerHTML = '';
      events.slice(0, 15).forEach(evt => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-surface-850/60 transition-colors";
        
        const badgeClass = evt.is_anomaly 
          ? "bg-rose-950/80 text-rose-300 border border-rose-800" 
          : "bg-emerald-950/80 text-emerald-300 border border-emerald-800";
        
        const badgeText = evt.is_anomaly ? "QUARANTINED" : "NOMINAL";
        const dateStr = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : "--:--:--";
        const mseVal = Number(evt.mse != null ? evt.mse : 0);
        const threshVal = Number(evt.threshold != null ? evt.threshold : 0);
        const resVal = Number(evt.root_cause_residual != null ? evt.root_cause_residual : 0);
        const latVal = Number(evt.latency_ms != null ? evt.latency_ms : 0);
        const scenarioName = (evt.scenario || 'unknown').toUpperCase();

        tr.innerHTML = `
          <td class="py-2.5 px-4">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">
              ${badgeText}
            </span>
          </td>
          <td class="py-2.5 px-4 text-slate-400 font-mono">${dateStr}</td>
          <td class="py-2.5 px-4 font-semibold ${evt.is_anomaly ? 'text-rose-400' : 'text-slate-200'}">
            ${scenarioName}
          </td>
          <td class="py-2.5 px-4 font-mono font-bold ${evt.is_anomaly ? 'text-rose-400' : 'text-emerald-400'}">
            ${mseVal.toFixed(5)} <span class="text-slate-500 font-normal">/ ${threshVal.toFixed(5)}</span>
          </td>
          <td class="py-2.5 px-4 font-mono text-cyan-400">
            ${evt.root_cause || 'nominal'} <span class="text-slate-500 text-[10px]">(${resVal.toFixed(4)})</span>
          </td>
          <td class="py-2.5 px-4 font-mono text-emerald-400">${latVal.toFixed(2)} ms</td>
          <td class="py-2.5 px-4 font-sans text-slate-400">${evt.mitigation || 'Normal Passthrough'}</td>
        `;
        tbody.appendChild(tr);
      });

      // Populate latest live/historical MSE into the chart if available
      if (events.length > 0) {
        const latestEvt = events[0];
        const latestMse = Number(latestEvt.mse != null ? latestEvt.mse : 0);
        document.getElementById('card-mse').innerText = latestMse.toFixed(5);
        if (latestEvt.latency_ms) {
          const lat = Number(latestEvt.latency_ms);
          document.getElementById('top-latency').innerText = `${lat.toFixed(2)} ms`;
          document.getElementById('mob-latency').innerText = `${lat.toFixed(2)} ms`;
          document.getElementById('card-latency').innerText = lat.toFixed(2);
        }
        if (mseChart && mseChart.data && mseChart.data.datasets && mseChart.data.datasets[0]) {
          const reversedEvents = [...events].reverse().slice(-20);
          if (reversedEvents.length > 0) {
            const mses = reversedEvents.map(e => Number(e.mse != null ? e.mse : 0.0005));
            while (mses.length < 20) mses.unshift(0.0005);
            mseChart.data.datasets[0].data = mses.slice(-20);
            mseChart.update();
          }
        }
      }
    }

    // Fetch Events API
    async function fetchEvents() {
      if (!isPolling) return;
      try {
        const res = await fetch('/v1/events');
        if (!res.ok) return;
        const events = await res.json();
        renderEvents(events);
      } catch (e) {
        console.warn('Events fetch error', e);
      }
    }

    // Fetch live status periodically
    async function updateStatus() {
      if (!isPolling) return;
      try {
        const res = await fetch('/v1/status');
        if (!res.ok) return;
        const data = await res.json();
        
        currentThreshold = Number(data.anomaly_threshold != null ? data.anomaly_threshold : 0.035);
        document.getElementById('top-threshold').innerText = currentThreshold.toFixed(6);
        document.getElementById('mob-threshold').innerText = currentThreshold.toFixed(6);
        document.getElementById('card-threshold').innerText = currentThreshold.toFixed(5);
        document.getElementById('card-device').innerText = data.device_type || 'Unknown';
        document.getElementById('card-inferences').innerText = data.total_inferences != null ? data.total_inferences : '--';
        
        const now = new Date();
        document.getElementById('last-updated-text').innerText = `Updated ${now.toLocaleTimeString()}`;

        if (data.edge_tpu_connected) {
          document.getElementById('tpu-pill').className = "inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 shrink-0";
          document.getElementById('tpu-pill').innerHTML = `<span class="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span><span class="hidden xs:inline">Coral </span>Active`;
        } else {
          document.getElementById('tpu-pill').className = "inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-950/80 text-amber-400 border border-amber-800/80 shrink-0";
          document.getElementById('tpu-pill').innerHTML = `<span class="h-1.5 w-1.5 rounded-full bg-amber-400 mr-1.5"></span>CPU Mode`;
        }

        if (mseChart && mseChart.data && mseChart.data.datasets && mseChart.data.datasets[1]) {
          mseChart.data.datasets[1].data = Array(20).fill(currentThreshold);
          mseChart.update();
        }
      } catch (e) {
        console.warn('Status poll error', e);
      }
    }

    // Interactive Scenario Injection
    async function injectScenario(type) {
      const vector = Array(32).fill(0.1);
      let desc = "";

      if (type === 'normal') {
        desc = "Normal baseline traffic (vector of standard benign flows)";
      } else if (type === 'syn_flood') {
        vector[0] = 0.85; // bytes rate
        vector[1] = 0.95; // pkts rate
        vector[4] = 0.98; // syn rate
        vector[9] = 0.99; // tcp ratio
        vector[21] = 0.80; // fw reject rate
        desc = "Injected SYN Flood attack pattern";
      } else if (type === 'dns_tunnel') {
        vector[16] = 0.92; // dns query rate
        vector[17] = 0.96; // dns nxdomain rate
        vector[18] = 0.99; // dns nxdomain ratio
        desc = "Injected DNS Tunneling / Exfiltration pattern";
      } else if (type === 'port_scan') {
        vector[14] = 0.95; // unique dst port
        vector[15] = 0.90; // fanout
        vector[21] = 0.88; // fw reject
        desc = "Injected Horizontal Port Scan pattern";
      }

      const simResult = document.getElementById('sim-result');
      simResult.classList.remove('hidden');
      document.getElementById('sim-text').innerText = `Dispatching ${type.toUpperCase()} to Edge TPU...`;

      try {
        const t0 = performance.now();
        const res = await fetch('/v1/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            features: vector,
            metadata: { scenario: type, manual: true }
          })
        });
        const latency = (performance.now() - t0).toFixed(2);
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || `Server returned ${res.status}`);
        }
        
        // Handle single or array return
        const result = Array.isArray(data) ? data[0] : data;
        const mse = Number(result.mse != null ? result.mse : (result.reconstruction_error_mse != null ? result.reconstruction_error_mse : 0));
        const latencyMs = Number(result.inference_latency_ms != null ? result.inference_latency_ms : latency);
        const isAnomaly = Boolean(result.is_anomaly);
        const devName = result.device === 'edgetpu' ? 'Edge TPU' : (result.device || 'TPU');

        document.getElementById('sim-text').innerHTML = `<span class="font-bold">${type.toUpperCase()}</span> &rarr; MSE: <span class="font-mono font-bold">${mse.toFixed(6)}</span> | Flag: <span class="${isAnomaly ? 'text-rose-400 font-bold' : 'text-emerald-400 font-semibold'}">${isAnomaly ? 'CRITICAL ANOMALY' : 'CLEAN'}</span>`;
        document.getElementById('sim-latency').innerText = `${latencyMs.toFixed(3)} ms (${devName})`;

        // Update top stats
        document.getElementById('top-latency').innerText = `${latencyMs.toFixed(2)} ms`;
        document.getElementById('mob-latency').innerText = `${latencyMs.toFixed(2)} ms`;
        document.getElementById('card-latency').innerText = latencyMs.toFixed(2);
        document.getElementById('card-mse').innerText = mse.toFixed(5);
        
        // Push to chart if initialized
        if (mseChart && mseChart.data && mseChart.data.datasets) {
          mseChart.data.datasets[0].data.shift();
          mseChart.data.datasets[0].data.push(mse);
          mseChart.data.datasets[1].data.shift();
          mseChart.data.datasets[1].data.push(currentThreshold);

          if (isAnomaly) {
            mseChart.data.datasets[0].borderColor = '#f43f5e';
            mseChart.data.datasets[0].backgroundColor = 'rgba(244, 63, 94, 0.18)';
          } else {
            mseChart.data.datasets[0].borderColor = '#10b981';
            mseChart.data.datasets[0].backgroundColor = 'rgba(16, 185, 129, 0.12)';
          }
          mseChart.update();
        }

        // Update colors based on anomaly
        if (isAnomaly) {
          document.getElementById('card-mse').className = "text-2xl sm:text-3xl font-bold font-mono text-rose-400 tracking-tight";
          document.getElementById('card-mse-bar').className = "bg-rose-500 h-full rounded-full transition-all duration-300";
          document.getElementById('card-mse-bar').style.width = "100%";
          document.getElementById('card-status-text').className = "text-rose-400 font-bold";
          document.getElementById('card-status-text').innerText = "ANOMALY DETECTED";
          
          document.getElementById('alert-banner').classList.remove('hidden');
          document.getElementById('alert-mse-value').innerText = `MSE: ${mse.toFixed(5)}`;
          anomaliesCount++;
          document.getElementById('card-anomalies-count').innerText = anomaliesCount;
        } else {
          document.getElementById('card-mse').className = "text-2xl sm:text-3xl font-bold font-mono text-emerald-400 tracking-tight";
          document.getElementById('card-mse-bar').className = "bg-emerald-400 h-full rounded-full transition-all duration-300";
          const thresh = currentThreshold > 0 ? currentThreshold : 0.035;
          const pct = Math.min(100, Math.round((mse / thresh) * 100));
          document.getElementById('card-mse-bar').style.width = `${pct}%`;
          document.getElementById('card-status-text').className = "text-emerald-400 font-medium";
          document.getElementById('card-status-text').innerText = "Nominal";
          document.getElementById('card-status-percent').innerText = `${pct}% of threshold`;
          document.getElementById('alert-banner').classList.add('hidden');
        }

        // Update residuals bar chart if initialized
        if (residualChart && residualChart.data && residualChart.data.datasets) {
          const residualsList = result.top_residuals || result.feature_residuals || [];
          if (residualsList.length > 0) {
            const sorted = [...residualsList].sort((a,b) => (Number(b.residual_mse ?? b.residual ?? 0)) - (Number(a.residual_mse ?? a.residual ?? 0))).slice(0, 5);
            residualChart.data.labels = sorted.map(s => s.feature_name);
            residualChart.data.datasets[0].data = sorted.map(s => Number(s.residual_mse ?? s.residual ?? 0));
            residualChart.data.datasets[0].backgroundColor = isAnomaly ? '#f43f5e' : '#06b6d4';
            residualChart.update();
          }
        }

        // Instantly refresh the Flagged Events table
        fetchEvents();

      } catch (e) {
        document.getElementById('sim-text').innerText = `Simulation failed: ${e.message || e}`;
      }
    }

    // Polling timers
    setInterval(updateStatus, 3000);
    setInterval(fetchEvents, 3000);
    updateStatus();
    fetchEvents();
  </script>

</body>
</html>
"""
