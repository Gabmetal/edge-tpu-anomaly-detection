"""
dashboard.py
Embedded Cyber SOC Dashboard for Edge TPU Anomaly Detection Microservice.
Served directly as modern responsive single-page application at '/' and '/ui'.
"""

def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Edge TPU Anomaly Detection SOC</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2306b6d4'><circle cx='12' cy='12' r='10'/></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
              800: '#1e293b',
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
  </style>
</head>
<body class="bg-surface-950 text-slate-100 font-sans min-h-screen flex flex-col antialiased selection:bg-brand-500 selection:text-white">

  <!-- Top Navigation Bar -->
  <header class="border-b border-slate-800 bg-surface-900/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="h-9 w-9 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
        <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      </div>
      <div>
        <div class="flex items-center space-x-2">
          <h1 class="text-base font-bold tracking-tight text-white">Edge TPU Cyber SOC</h1>
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800" id="tpu-pill">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
            Coral TPU Active
          </span>
        </div>
        <p class="text-xs text-slate-400">Homelab K3s &bull; Bare-Metal Anomaly Detection &bull; OpenWrt Telemetry</p>
      </div>
    </div>

    <!-- Quick Status Badges -->
    <div class="flex items-center space-x-3 text-xs">
      <div class="hidden sm:flex items-center space-x-2 bg-surface-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
        <span class="text-slate-400">Threshold:</span>
        <span class="font-mono text-brand-400 font-semibold" id="top-threshold">0.001806</span>
      </div>
      <div class="flex items-center space-x-2 bg-surface-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
        <span class="text-slate-400">Last Latency:</span>
        <span class="font-mono text-emerald-400 font-bold" id="top-latency">0.38 ms</span>
      </div>
      <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition">Swagger API</a>
      <a href="https://grafana.gabo.lat" target="_blank" class="px-3 py-1.5 rounded-lg bg-indigo-900/60 hover:bg-indigo-800/80 border border-indigo-700/60 text-indigo-300 hover:text-white transition flex items-center space-x-1">
        <span>Grafana</span>
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
      </a>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">

    <!-- Anomaly Alert Banner (Conditional) -->
    <div id="alert-banner" class="hidden rounded-xl border border-rose-500/40 bg-rose-950/40 p-4 backdrop-blur shadow-lg shadow-rose-950/40 flex items-start space-x-4">
      <div class="h-10 w-10 rounded-lg bg-rose-500/20 border border-rose-500/50 flex items-center justify-center text-rose-400 shrink-0">
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
      </div>
      <div class="flex-1">
        <h3 class="text-sm font-bold text-rose-300 uppercase tracking-wide">Anomaly Detected &bull; Reconstruction Loss Breach</h3>
        <p class="text-xs text-rose-200/80 mt-0.5" id="alert-detail">Latest 10-second telemetry window yielded an autoencoder MSE loss significantly above normal operational baseline.</p>
      </div>
      <div class="text-right">
        <span class="inline-block px-2.5 py-1 rounded bg-rose-500/20 text-rose-300 font-mono text-xs font-bold border border-rose-500/30" id="alert-mse-value">MSE: 0.0450</span>
      </div>
    </div>

    <!-- Top KPI Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- Card 1: Live MSE -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div class="flex items-center justify-between text-xs text-slate-400">
          <span>Reconstruction Error</span>
          <span class="font-mono text-[10px] text-slate-500">MSE Loss</span>
        </div>
        <div class="mt-2 flex items-baseline space-x-2">
          <span class="text-2xl font-bold font-mono text-emerald-400" id="card-mse">0.00052</span>
          <span class="text-xs text-slate-500 font-mono">/ <span id="card-threshold">0.00180</span></span>
        </div>
        <div class="mt-3 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
          <div id="card-mse-bar" class="bg-emerald-400 h-full rounded-full transition-all duration-300" style="width: 25%"></div>
        </div>
        <div class="mt-2 text-[11px] text-slate-400 flex justify-between">
          <span>Status: <span id="card-status-text" class="text-emerald-400 font-medium">Nominal</span></span>
          <span id="card-status-percent" class="font-mono text-slate-500">28% of threshold</span>
        </div>
      </div>

      <!-- Card 2: TPU Accelerator Latency -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div class="flex items-center justify-between text-xs text-slate-400">
          <span>Hardware Execution Time</span>
          <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-brand-950 text-brand-400 border border-brand-800">SLA &lt; 2ms</span>
        </div>
        <div class="mt-2 flex items-baseline space-x-2">
          <span class="text-2xl font-bold font-mono text-brand-400" id="card-latency">0.38</span>
          <span class="text-xs text-slate-400">ms / eval</span>
        </div>
        <div class="mt-3 text-[11px] text-slate-400 flex items-center justify-between">
          <span>Accelerator: <span class="text-slate-300 font-mono" id="card-device">Google Coral USB</span></span>
          <span class="text-emerald-400 font-mono text-[10px]">INT8 Systolic</span>
        </div>
      </div>

      <!-- Card 3: Inferences Count -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div class="flex items-center justify-between text-xs text-slate-400">
          <span>Total Inferences</span>
          <span class="text-[10px] text-slate-500">10s Windows</span>
        </div>
        <div class="mt-2 flex items-baseline space-x-2">
          <span class="text-2xl font-bold font-mono text-white" id="card-inferences">0</span>
          <span class="text-xs text-slate-400">evals</span>
        </div>
        <div class="mt-3 text-[11px] text-slate-400 flex justify-between">
          <span>Anomalies Flagged:</span>
          <span class="font-mono text-rose-400 font-bold" id="card-anomalies-count">0</span>
        </div>
      </div>

      <!-- Card 4: OpenWrt & K8s Pipeline -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div class="flex items-center justify-between text-xs text-slate-400">
          <span>Telemetry Ingress</span>
          <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
        </div>
        <div class="mt-2 flex items-baseline space-x-2">
          <span class="text-sm font-semibold text-slate-200">Vector MetalLB VIP</span>
        </div>
        <div class="mt-1 font-mono text-xs text-brand-400">192.168.0.52</div>
        <div class="mt-2 text-[11px] text-slate-400 flex justify-between">
          <span>Syslog: 514 UDP</span>
          <span>NetFlow: 2055 UDP</span>
        </div>
      </div>

    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Chart: Live MSE Rolling Window -->
      <div class="lg:col-span-2 bg-surface-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-sm font-bold text-white tracking-wide">Live Autoencoder Reconstruction Error (MSE)</h2>
            <p class="text-xs text-slate-400 mt-0.5">Sliding telemetry window evaluation against baseline calibration</p>
          </div>
          <span class="px-2 py-1 bg-slate-800 rounded text-xs font-mono text-slate-300">Live (3s update)</span>
        </div>
        <div class="h-64 relative">
          <canvas id="mseChart"></canvas>
        </div>
      </div>

      <!-- Chart: 32-D Feature Residual Breakdown -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-sm font-bold text-white tracking-wide">Top Feature Residuals</h2>
            <p class="text-xs text-slate-400 mt-0.5">Root-cause contribution $(x_i - \hat{x}_i)^2$</p>
          </div>
        </div>
        <div class="h-64 relative">
          <canvas id="residualChart"></canvas>
        </div>
      </div>

    </div>

    <!-- Interactive Attack Injection & Diagnostic Workbench -->
    <div class="bg-surface-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-4 mb-4">
        <div>
          <h2 class="text-sm font-bold text-white tracking-wide">Interactive Telemetry & Attack Simulation</h2>
          <p class="text-xs text-slate-400 mt-0.5">Send test vectors directly into the Edge TPU neural inference loop to verify detection & alerts</p>
        </div>
        <div class="text-xs text-slate-500 font-mono">
          Endpoint: <code class="text-slate-300">POST /v1/predict</code>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <!-- Button 1: Normal Baseline -->
        <button onclick="injectScenario('normal')" class="p-3 bg-surface-800 hover:bg-slate-700/80 border border-slate-700 rounded-lg text-left transition flex flex-col justify-between group">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-emerald-400">Normal Baseline</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-emerald-950/60 border border-emerald-800 rounded text-emerald-300">Clean</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">Simulates typical network flow, DNS queries, and cluster activity.</p>
          <span class="text-[10px] text-brand-400 font-mono mt-3 block group-hover:underline">&rarr; Inject Vector</span>
        </button>

        <!-- Button 2: SYN Flood Attack -->
        <button onclick="injectScenario('syn_flood')" class="p-3 bg-surface-800 hover:bg-rose-950/40 border border-rose-900/50 hover:border-rose-600 rounded-lg text-left transition flex flex-col justify-between group">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-rose-400">SYN Flood Surge</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-rose-950/60 border border-rose-800 rounded text-rose-300">Attack</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">High packet rate, low packet size, 98% TCP SYN ratio anomaly.</p>
          <span class="text-[10px] text-rose-400 font-mono mt-3 block group-hover:underline">&rarr; Inject Vector</span>
        </button>

        <!-- Button 3: DNS Exfiltration / Tunnel -->
        <button onclick="injectScenario('dns_tunnel')" class="p-3 bg-surface-800 hover:bg-amber-950/40 border border-amber-900/50 hover:border-amber-600 rounded-lg text-left transition flex flex-col justify-between group">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-amber-400">DNS Tunneling</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-amber-950/60 border border-amber-800 rounded text-amber-300">Attack</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">Surging NXDOMAIN rates, high query frequency, DGA beaconing.</p>
          <span class="text-[10px] text-amber-400 font-mono mt-3 block group-hover:underline">&rarr; Inject Vector</span>
        </button>

        <!-- Button 4: Port Scan -->
        <button onclick="injectScenario('port_scan')" class="p-3 bg-surface-800 hover:bg-purple-950/40 border border-purple-900/50 hover:border-purple-600 rounded-lg text-left transition flex flex-col justify-between group">
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-bold text-purple-400">Port Scan Sweep</span>
            <span class="text-[10px] px-1.5 py-0.5 bg-purple-950/60 border border-purple-800 rounded text-purple-300">Attack</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">High unique destination ports, elevated firewall reject rate.</p>
          <span class="text-[10px] text-purple-400 font-mono mt-3 block group-hover:underline">&rarr; Inject Vector</span>
        </button>
      </div>

      <div id="sim-result" class="hidden mt-4 p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-xs text-slate-300 flex items-center justify-between">
        <span id="sim-text">Simulation dispatched</span>
        <span id="sim-latency" class="text-emerald-400 font-bold"></span>
      </div>
    </div>

    <!-- Router & Infrastructure Details -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- OpenWrt Node Info -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
          <span>OpenWrt Telemetry Node</span>
          <span class="font-mono text-[10px] text-emerald-400">192.168.0.1</span>
        </h3>
        <dl class="space-y-2 text-xs">
          <div class="flex justify-between py-1 border-b border-slate-800/60">
            <dt class="text-slate-400">Router Platform:</dt>
            <dd class="font-mono text-slate-200">OpenWrt 23.05.2 (mipsel_24kc MT7621)</dd>
          </div>
          <div class="flex justify-between py-1 border-b border-slate-800/60">
            <dt class="text-slate-400">Firewall Architecture:</dt>
            <dd class="font-mono text-slate-200">nftables (fw4) &bull; banIP</dd>
          </div>
          <div class="flex justify-between py-1 border-b border-slate-800/60">
            <dt class="text-slate-400">Automated Quarantine Set:</dt>
            <dd class="font-mono text-brand-400">inet fw4 quarantined_hosts</dd>
          </div>
          <div class="flex justify-between py-1">
            <dt class="text-slate-400">AdGuard Home DNS:</dt>
            <dd class="font-mono text-slate-200">http://192.168.0.1:8080</dd>
          </div>
        </dl>
      </div>

      <!-- K3s Host Info -->
      <div class="bg-surface-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
          <span>K3s Edge ML Hardware</span>
          <span class="font-mono text-[10px] text-brand-400">xeon</span>
        </h3>
        <dl class="space-y-2 text-xs">
          <div class="flex justify-between py-1 border-b border-slate-800/60">
            <dt class="text-slate-400">Coral Edge TPU Device:</dt>
            <dd class="font-mono text-emerald-400">/dev/bus/usb/003/003 (18d1:9302)</dd>
          </div>
          <div class="flex justify-between py-1 border-b border-slate-800/60">
            <dt class="text-slate-400">Runtime Delegate:</dt>
            <dd class="font-mono text-slate-200">libedgetpu.so.1 (Standard 16.0)</dd>
          </div>
          <div class="flex justify-between py-1 border-b border-slate-800/60">
            <dt class="text-slate-400">Autoencoder Architecture:</dt>
            <dd class="font-mono text-slate-200">Dense(16) &rarr; Dense(8) &rarr; Dense(16) [INT8]</dd>
          </div>
          <div class="flex justify-between py-1">
            <dt class="text-slate-400">Ingress Route:</dt>
            <dd class="font-mono text-indigo-400">https://anomaly.gabo.lat (Cloudflare Access)</dd>
          </div>
        </dl>
      </div>

    </div>

  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800/80 bg-surface-900/40 text-center py-4 text-xs text-slate-500">
    Edge ML Cyber Infrastructure &bull; Bare-Metal K3s &bull; Coral Edge TPU INT8 Acceleration &bull; Zero-Trust Zero-Cloud
  </footer>

  <!-- Dashboard JavaScript Logic -->
  <script>
    let currentThreshold = 0.001806;
    let totalInferences = 0;
    let anomaliesCount = 0;

    // Feature Names matching 32-D vector
    const featureNames = [
      "bytes_rate", "pkts_rate", "avg_pkt_sz", "avg_dur",
      "syn_rate", "fin_rate", "rst_rate", "syn_fin_ratio",
      "rst_ratio", "tcp_ratio", "udp_ratio", "icmp_ratio",
      "uniq_src_ip", "uniq_dst_ip", "uniq_dst_port", "fanout_ratio",
      "dns_query_rate", "dns_nx_rate", "dns_nx_ratio", "adblock_drop_rate",
      "adblock_drop_ratio", "fw_reject_rate", "fw_syn_drop_rate", "fw_out_drop_rate",
      "k8s_req_rate", "k8s_401_rate", "k8s_403_rate", "k8s_err_ratio",
      "k8s_exec_probe", "k8s_priv_escalate", "k8s_anon_req", "k8s_churn_rate"
    ];

    // Chart.js: MSE Trend Chart
    const ctxMse = document.getElementById('mseChart').getContext('2d');
    const mseData = {
      labels: Array(20).fill(''),
      datasets: [
        {
          label: 'Reconstruction Loss (MSE)',
          data: Array(20).fill(0.0005),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 2
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
    const mseChart = new Chart(ctxMse, {
      type: 'line',
      data: mseData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8', boxWidth: 12, font: { size: 11 } } }
        },
        scales: {
          x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { display: false } },
          y: {
            grid: { color: 'rgba(51, 65, 85, 0.3)' },
            ticks: { color: '#94a3b8', font: { family: 'monospace', size: 10 } },
            suggestedMin: 0,
            suggestedMax: 0.005
          }
        }
      }
    });

    // Chart.js: Feature Residual Horizontal Bar
    const ctxResidual = document.getElementById('residualChart').getContext('2d');
    const residualChart = new Chart(ctxResidual, {
      type: 'bar',
      data: {
        labels: ['tcp_ratio', 'syn_rate', 'fw_reject_rate', 'dns_nx_ratio', 'k8s_err_ratio'],
        datasets: [{
          label: 'Residual Score',
          data: [0.01, 0.008, 0.005, 0.003, 0.002],
          backgroundColor: '#06b6d4',
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#94a3b8', font: { size: 9 } } },
          y: { grid: { display: false }, ticks: { color: '#cbd5e1', font: { size: 10 } } }
        }
      }
    });

    // Fetch live status periodically
    async function updateStatus() {
      try {
        const res = await fetch('/v1/status');
        if (!res.ok) return;
        const data = await res.json();
        
        currentThreshold = data.anomaly_threshold;
        document.getElementById('top-threshold').innerText = currentThreshold.toFixed(6);
        document.getElementById('card-threshold').innerText = currentThreshold.toFixed(5);
        document.getElementById('card-device').innerText = data.device_type;
        document.getElementById('card-inferences').innerText = data.total_inferences;
        
        if (data.edge_tpu_connected) {
          document.getElementById('tpu-pill').className = "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800";
          document.getElementById('tpu-pill').innerHTML = `<span class="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>Coral TPU Active`;
        } else {
          document.getElementById('tpu-pill').className = "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-950 text-amber-400 border border-amber-800";
          document.getElementById('tpu-pill').innerHTML = `<span class="h-1.5 w-1.5 rounded-full bg-amber-400 mr-1.5"></span>CPU Fallback Mode`;
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
        
        // Handle single or array return
        const result = Array.isArray(data) ? data[0] : data;

        document.getElementById('sim-text').innerText = `${type.toUpperCase()} &rarr; MSE: ${result.reconstruction_error_mse.toFixed(6)} | Flag: ${result.is_anomaly ? 'CRITICAL ANOMALY' : 'CLEAN'}`;
        document.getElementById('sim-latency').innerText = `${result.inference_latency_ms.toFixed(3)} ms (TPU)`;

        // Update top stats
        document.getElementById('top-latency').innerText = `${result.inference_latency_ms.toFixed(2)} ms`;
        document.getElementById('card-latency').innerText = result.inference_latency_ms.toFixed(2);
        document.getElementById('card-mse').innerText = result.reconstruction_error_mse.toFixed(5);
        
        // Push to chart
        mseChart.data.datasets[0].data.shift();
        mseChart.data.datasets[0].data.push(result.reconstruction_error_mse);
        mseChart.data.datasets[1].data.shift();
        mseChart.data.datasets[1].data.push(currentThreshold);

        // Update colors based on anomaly
        if (result.is_anomaly) {
          mseChart.data.datasets[0].borderColor = '#f43f5e';
          mseChart.data.datasets[0].backgroundColor = 'rgba(244, 63, 94, 0.15)';
          document.getElementById('card-mse').className = "text-2xl font-bold font-mono text-rose-400";
          document.getElementById('card-mse-bar').className = "bg-rose-500 h-full rounded-full transition-all duration-300";
          document.getElementById('card-mse-bar').style.width = "100%";
          document.getElementById('card-status-text').className = "text-rose-400 font-bold";
          document.getElementById('card-status-text').innerText = "ANOMALY DETECTED";
          
          document.getElementById('alert-banner').classList.remove('hidden');
          document.getElementById('alert-mse-value').innerText = `MSE: ${result.reconstruction_error_mse.toFixed(5)}`;
          anomaliesCount++;
          document.getElementById('card-anomalies-count').innerText = anomaliesCount;
        } else {
          mseChart.data.datasets[0].borderColor = '#10b981';
          mseChart.data.datasets[0].backgroundColor = 'rgba(16, 185, 129, 0.1)';
          document.getElementById('card-mse').className = "text-2xl font-bold font-mono text-emerald-400";
          document.getElementById('card-mse-bar').className = "bg-emerald-400 h-full rounded-full transition-all duration-300";
          const pct = Math.min(100, Math.round((result.reconstruction_error_mse / currentThreshold) * 100));
          document.getElementById('card-mse-bar').style.width = `${pct}%`;
          document.getElementById('card-status-text').className = "text-emerald-400 font-medium";
          document.getElementById('card-status-text').innerText = "Nominal";
          document.getElementById('card-status-percent').innerText = `${pct}% of threshold`;
          document.getElementById('alert-banner').classList.add('hidden');
        }
        mseChart.update();

        // Update residuals bar chart
        if (result.feature_residuals && result.feature_residuals.length > 0) {
          const sorted = [...result.feature_residuals].sort((a,b) => b.residual - a.residual).slice(0, 5);
          residualChart.data.labels = sorted.map(s => s.feature_name);
          residualChart.data.datasets[0].data = sorted.map(s => s.residual);
          residualChart.data.datasets[0].backgroundColor = result.is_anomaly ? '#f43f5e' : '#06b6d4';
          residualChart.update();
        }

      } catch (e) {
        document.getElementById('sim-text').innerText = `Simulation failed: ${e}`;
      }
    }

    // Polling timer
    setInterval(updateStatus, 3000);
    updateStatus();
  </script>

</body>
</html>
"""
