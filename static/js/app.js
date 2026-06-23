/**
 * FaceForm AI — Frontend Application
 * Handles: upload, drag & drop, API calls, chart rendering, history, health status
 */

"use strict";

// ── Constants ─────────────────────────────────────────────────────────────────
const MAX_SIZE_BYTES = 8 * 1024 * 1024; // 8MB client-side check
const MAX_DIM = 1200; // resize larger images before upload

const SHAPE_DESCRIPTIONS = {
  Heart:  "A heart-shaped face features a wider forehead that tapers down to a narrow, pointed chin. This shape is often associated with high cheekbones and a delicate jawline.",
  Oblong: "An oblong face is longer than it is wide, with a straight jawline and forehead of similar width. The face appears elongated and narrow, giving a refined, distinguished look.",
  Oval:   "An oval face has balanced proportions with a slightly wider forehead than jawline. Often considered the most versatile shape — most hairstyles and accessories suit it well.",
  Round:  "A round face has full cheeks and a gentle jawline, with width and length in approximately equal proportions. Soft, curved contours define this friendly, approachable shape.",
  Square: "A square face is characterized by a strong, angular jawline and a broad forehead with similar widths at all three points: forehead, cheekbones, and jaw.",
};

const CHART_COLORS = {
  active: { bg: "rgba(110,231,199,0.85)", border: "#6EE7C7" },
  dim:    { bg: "rgba(30,45,60,0.8)",     border: "rgba(255,255,255,0.08)" },
};

// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  selectedFile: null,
  previewUrl: null,
  selectedGender: null,
  isLoading: false,
  probChart: null,
  history: [],
};

// ── DOM References ────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

const dom = {
  dropzone:       $("dropzone"),
  dropzoneIdle:   $("dropzoneIdle"),
  dropzonePreview:$("dropzonePreview"),
  previewImg:     $("previewImg"),
  fileInput:      $("fileInput"),
  btnRemove:      $("btnRemove"),
  btnAnalyze:     $("btnAnalyze"),
  imageInfo:      $("imageInfo"),
  errorBanner:    $("errorBanner"),
  errorMsg:       $("errorMsg"),
  apiKeyInput:    $("apiKeyInput"),
  resultsPanel:   $("resultsPanel"),
  resultsEmpty:   $("resultsEmpty"),
  resultsContent: $("resultsContent"),
  predName:       $("predName"),
  confBadge:      $("confBadge"),
  confValue:      $("confValue"),
  shapeDesc:      $("shapeDesc"),
  probBars:       $("probBars"),
  resultTime:     $("resultTime"),
  resultReqId:    $("resultReqId"),
  historySection: $("historySection"),
  historyList:    $("historyList"),
  btnClearHistory:$("btnClearHistory"),
  statusDot:       $("statusDot"),
  statusText:      $("statusText"),
  genderMale:      $("genderMale"),
  genderFemale:    $("genderFemale"),
  recPanel:        $("recommendationsPanel"),
  recSpecificTitle:$("recSpecificTitle"),
  recTipText:      $("recTipText"),
  recTip:          $("recTip"),
};

// ── Utility Functions ─────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function showError(msg) {
  dom.errorMsg.textContent = msg;
  dom.errorBanner.style.display = "flex";
  setTimeout(() => dom.errorBanner.style.display = "none", 6000);
}

function hideError() {
  dom.errorBanner.style.display = "none";
}

function setLoading(val) {
  state.isLoading = val;
  dom.btnAnalyze.classList.toggle("loading", val);
  const notReady = val || !state.selectedFile || !state.selectedGender;
  dom.btnAnalyze.disabled = notReady;
  dom.btnAnalyze.setAttribute("aria-disabled", String(notReady));
}

// ── Gender Selection ──────────────────────────────────────────────────────────
function selectGender(gender) {
  state.selectedGender = gender;
  dom.genderMale.classList.toggle("active", gender === "male");
  dom.genderFemale.classList.toggle("active", gender === "female");
  dom.genderMale.setAttribute("aria-pressed", String(gender === "male"));
  dom.genderFemale.setAttribute("aria-pressed", String(gender === "female"));
  // Re-evaluate button state
  const notReady = !state.selectedFile || !state.selectedGender;
  dom.btnAnalyze.disabled = notReady;
  dom.btnAnalyze.setAttribute("aria-disabled", String(notReady));
}

// ── Image Resizing (client-side) ───────────────────────────────────────────────
function resizeImageIfNeeded(file) {
  return new Promise((resolve) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      if (img.width <= MAX_DIM && img.height <= MAX_DIM) {
        resolve(file); // no resize needed
        return;
      }
      const scale = MAX_DIM / Math.max(img.width, img.height);
      const canvas = document.createElement("canvas");
      canvas.width  = Math.round(img.width  * scale);
      canvas.height = Math.round(img.height * scale);
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        resolve(new File([blob], file.name, { type: "image/jpeg" }));
      }, "image/jpeg", 0.92);
    };
    img.src = url;
  });
}

// ── Convert File → base64 data URL (thumbnail, persistent) ──────────────────
function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      const MAX = 200;
      const scale = Math.min(1, MAX / Math.max(img.width, img.height));
      const canvas = document.createElement("canvas");
      canvas.width  = Math.round(img.width  * scale);
      canvas.height = Math.round(img.height * scale);
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      resolve(canvas.toDataURL("image/jpeg", 0.75));
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("img load")); };
    img.src = url;
  });
}

// ── File Handling ─────────────────────────────────────────────────────────────
function handleFile(file) {
  hideError();

  // Validate type
  const allowed = ["image/jpeg", "image/png", "image/jpg"];
  if (!allowed.includes(file.type)) {
    showError("Invalid file type. Please upload a JPG or PNG image.");
    return;
  }

  // Validate size
  if (file.size > MAX_SIZE_BYTES) {
    showError(`File too large (${formatBytes(file.size)}). Max: 8MB.`);
    return;
  }

  state.selectedFile = file;

  // Show preview
  if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
  state.previewUrl = URL.createObjectURL(file);
  dom.previewImg.src = state.previewUrl;
  dom.previewImg.alt = `Preview of ${file.name}`;
  dom.dropzoneIdle.style.display = "none";
  dom.dropzonePreview.style.display = "block";
  dom.imageInfo.textContent = `${file.name} · ${formatBytes(file.size)}`;

  // Enable analyze button
  dom.btnAnalyze.disabled = false;
  dom.btnAnalyze.setAttribute("aria-disabled", "false");
}

function clearFile() {
  state.selectedFile = null;
  if (state.previewUrl) {
    URL.revokeObjectURL(state.previewUrl);
    state.previewUrl = null;
  }
  dom.previewImg.src = "";
  dom.previewImg.alt = "";
  dom.dropzonePreview.style.display = "none";
  dom.dropzoneIdle.style.display = "flex";
  dom.imageInfo.textContent = "";
  dom.fileInput.value = "";
  dom.btnAnalyze.disabled = true;
  dom.btnAnalyze.setAttribute("aria-disabled", "true");
  hideError();
}

// ── Drag & Drop ───────────────────────────────────────────────────────────────
function setupDragDrop() {
  const dz = dom.dropzone;

  dz.addEventListener("dragenter", (e) => { e.preventDefault(); dz.classList.add("drag-over"); });
  dz.addEventListener("dragover",  (e) => { e.preventDefault(); dz.classList.add("drag-over"); });
  dz.addEventListener("dragleave", (e) => { if (!dz.contains(e.relatedTarget)) dz.classList.remove("drag-over"); });
  dz.addEventListener("drop", (e) => {
    e.preventDefault();
    dz.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  dz.addEventListener("click", (e) => {
    if (e.target !== dom.btnRemove && !dom.btnRemove.contains(e.target)) {
      dom.fileInput.click();
    }
  });

  dz.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      dom.fileInput.click();
    }
  });

  dom.fileInput.addEventListener("change", () => {
    if (dom.fileInput.files[0]) handleFile(dom.fileInput.files[0]);
  });

  dom.btnRemove.addEventListener("click", (e) => {
    e.stopPropagation();
    clearFile();
  });
}

// ── API Call ──────────────────────────────────────────────────────────────────
async function runPrediction() {
  if (!state.selectedFile || state.isLoading) return;

  hideError();
  setLoading(true);

  try {
    // Resize if needed before upload
    const fileToSend = await resizeImageIfNeeded(state.selectedFile);

    if (!state.selectedGender) {
      showError("Please select your gender before analyzing.");
      return;
    }

    const formData = new FormData();
    formData.append("image", fileToSend);
    formData.append("gender", state.selectedGender);

    const apiKey = dom.apiKeyInput.value.trim() || "dev-key-change-me";

    const response = await fetch("/api/predict", {
      method: "POST",
      headers: { "X-API-KEY": apiKey },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok || data.status === "error") {
      showError(data.message || `Request failed (${response.status})`);
      return;
    }

    displayResults(data, state.previewUrl);
    displayRecommendations(data);
    // Convert to base64 thumbnail so history img survives URL revocation
    try {
      const thumbDataUrl = await fileToDataUrl(state.selectedFile);
      addToHistory(data, thumbDataUrl);
    } catch {
      addToHistory(data, state.previewUrl); // fallback
    }

  } catch (err) {
    showError("Network error. Is the server running?");
    console.error("Prediction error:", err);
  } finally {
    setLoading(false);
  }
}

// ── Results Display ───────────────────────────────────────────────────────────
function displayResults(data, previewUrl) {
  const { prediction, confidence, probs, processing_time_ms, request_id } = data;

  // Prediction header
  dom.predName.textContent = prediction;
  dom.confValue.textContent = `${Math.round(confidence * 100)}%`;

  // Confidence color
  const confPct = confidence * 100;
  dom.confBadge.style.borderColor =
    confPct >= 75 ? "rgba(110,231,199,0.4)" :
    confPct >= 50 ? "rgba(251,191,36,0.4)"  :
                    "rgba(248,113,113,0.4)";

  // Shape description
  dom.shapeDesc.textContent = SHAPE_DESCRIPTIONS[prediction] || "";

  // Sort probs descending
  const sortedProbs = Object.entries(probs).sort(([,a],[,b]) => b - a);

  // Probability bars (text)
  dom.probBars.innerHTML = sortedProbs.map(([cls, prob]) => {
    const pct = Math.round(prob * 100);
    const isTop = cls === prediction;
    return `
      <div class="prob-bar-item" role="row">
        <span class="prob-bar-label" role="rowheader">${cls}</span>
        <div class="prob-bar-track" role="cell" aria-label="${cls}: ${pct}%">
          <div class="prob-bar-fill${isTop ? "" : " dim"}" style="width:${pct}%"></div>
        </div>
        <span class="prob-bar-value" role="cell">${pct}%</span>
      </div>`;
  }).join("");

  // Chart
  renderChart(sortedProbs, prediction);

  // Meta
  dom.resultTime.textContent = `⏱ ${processing_time_ms} ms`;
  dom.resultReqId.textContent = request_id ? `#${request_id}` : "";

  // Show results
  dom.resultsEmpty.style.display = "none";
  dom.resultsContent.style.display = "block";
}

// ── Recommendations Display ───────────────────────────────────────────────────
function makeVisualCard(item, index) {
  const hasImg = item.image && item.image.length > 0;
  const num = String(index + 1).padStart(2, "0");
  return `
    <div class="vis-card ${hasImg ? "has-img" : ""}"
         role="button" tabindex="0"
         data-img="${item.image || ""}" data-name="${item.name}"
         data-index="${num}"
         aria-label="Preview ${item.name}">
      ${hasImg ? `
        <div class="vis-card-img-wrap">
          <img class="vis-card-img" src="${item.image}" alt="${item.name}" loading="lazy" />
          <div class="vis-card-overlay">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          </div>
        </div>` : `
        <div class="vis-card-img-wrap vis-card-no-img">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        </div>`}
      <div class="vis-card-info">
        <span class="vis-card-name">${item.name}</span>
        <span class="vis-card-desc">${item.desc || ""}</span>
      </div>
    </div>`;
}

function makeTipCard(item) {
  return `
    <div class="tip-card">
      <span class="tip-card-dot"></span>
      <div>
        <span class="tip-card-name">${item.name}</span>
        <span class="tip-card-desc">${item.desc || ""}</span>
      </div>
    </div>`;
}

function displayRecommendations(data) {
  const { recommendations, gender } = data;
  if (!recommendations || Object.keys(recommendations).length === 0) {
    dom.recPanel.style.display = "none";
    return;
  }

  // Hairstyle visual gallery
  const hairstyleEl = document.getElementById("hairstyleGallery");
  if (hairstyleEl) hairstyleEl.innerHTML = (recommendations.hairstyle || []).map((item, i) => makeVisualCard(item, i)).join("");

  // Glasses visual gallery
  const glassesEl = document.getElementById("glassesGallery");
  if (glassesEl) glassesEl.innerHTML = (recommendations.glasses || []).map((item, i) => makeVisualCard(item, i)).join("");

  // Specific tips (beard / makeup)
  dom.recSpecificTitle.textContent = recommendations.specific_label || (gender === "male" ? "Beard Style" : "Makeup Tips");
  const specificEl = document.getElementById("recSpecificList");
  if (specificEl) specificEl.innerHTML = (recommendations.specific || []).map(makeTipCard).join("");

  // Pro tip
  if (recommendations.tip) {
    dom.recTipText.textContent = recommendations.tip;
    dom.recTip.style.display = "flex";
  } else {
    dom.recTip.style.display = "none";
  }

  dom.recPanel.style.display = "block";

  // Attach lightbox listeners to visual cards
  document.querySelectorAll(".vis-card.has-img").forEach(card => {
    const open = () => openLightbox(card.dataset.img, card.dataset.name);
    card.addEventListener("click", open);
    card.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
    });
  });
}

// ── Lightbox ──────────────────────────────────────────────────────────────────
function openLightbox(src, caption) {
  const lb = document.getElementById("lightbox");
  document.getElementById("lightboxImg").src = src;
  document.getElementById("lightboxImg").alt = caption;
  document.getElementById("lightboxCaption").textContent = caption;
  lb.style.display = "flex";
  document.getElementById("lightboxClose").focus();
}

function closeLightbox() {
  document.getElementById("lightbox").style.display = "none";
}

// ── Chart Rendering ───────────────────────────────────────────────────────────
function renderChart(sortedProbs, topClass) {
  const labels = sortedProbs.map(([cls]) => cls);
  const values = sortedProbs.map(([,p]) => Math.round(p * 1000) / 10);
  const bgColors = sortedProbs.map(([cls]) =>
    cls === topClass ? CHART_COLORS.active.bg : CHART_COLORS.dim.bg
  );
  const borderColors = sortedProbs.map(([cls]) =>
    cls === topClass ? CHART_COLORS.active.border : CHART_COLORS.dim.border
  );

  if (state.probChart) {
    state.probChart.data.labels = labels;
    state.probChart.data.datasets[0].data = values;
    state.probChart.data.datasets[0].backgroundColor = bgColors;
    state.probChart.data.datasets[0].borderColor = borderColors;
    state.probChart.update("active");
    return;
  }

  const ctx = document.getElementById("probChart").getContext("2d");
  state.probChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: bgColors,
        borderColor: borderColors,
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 600, easing: "easeOutQuart" },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.raw.toFixed(1)}%`,
          },
          backgroundColor: "rgba(13,17,23,0.95)",
          borderColor: "rgba(255,255,255,0.08)",
          borderWidth: 1,
          titleColor: "#e8edf2",
          bodyColor: "#8899aa",
          padding: 10,
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(255,255,255,0.04)" },
          ticks: { color: "#8899aa", font: { size: 12 } },
          border: { color: "rgba(255,255,255,0.04)" },
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: "rgba(255,255,255,0.04)" },
          ticks: {
            color: "#8899aa",
            font: { size: 11 },
            callback: (v) => `${v}%`,
          },
          border: { color: "rgba(255,255,255,0.04)" },
        },
      },
    },
  });
}

// ── Session History ────────────────────────────────────────────────────────────
function addToHistory(data, previewUrl) {
  const entry = {
    id: data.request_id || Date.now().toString(),
    prediction: data.prediction,
    confidence: data.confidence,
    gender: data.gender || state.selectedGender,
    previewUrl,
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  };

  state.history.unshift(entry);
  if (state.history.length > 8) state.history.pop();

  renderHistory();
  dom.historySection.style.display = "block";
}

function renderHistory() {
  dom.historyList.innerHTML = state.history.map((item) => {
    const pct = Math.round(item.confidence * 100);
    const confColor = pct >= 75 ? "#6EE7C7" : pct >= 50 ? "#fbbf24" : "#f87171";
    const genderIcon = item.gender === "male" ? "♂" : item.gender === "female" ? "♀" : "";
    return `
    <div class="history-item" role="listitem">
      <img class="history-thumb" src="${item.previewUrl}" alt="Face shape: ${item.prediction}" />
      <div class="history-info">
        <p class="history-pred">${item.prediction} <span class="history-gender">${genderIcon}</span></p>
        <p class="history-conf" style="color:${confColor}">${pct}% confidence</p>
      </div>
      <span class="history-time">${item.time}</span>
    </div>`;
  }).join("");
}

function clearHistory() {
  // History items use base64 data URLs — no revocation needed
  state.history = [];
  dom.historyList.innerHTML = "";
  dom.historySection.style.display = "none";
}

// ── Health Check ──────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch("/api/health", { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    const online = data.status === "ok" && data.model_loaded;
    dom.statusDot.className = `status-dot ${online ? "online" : "offline"}`;
    dom.statusText.textContent = online ? "API Online" : "Model Loading…";
  } catch {
    dom.statusDot.className = "status-dot offline";
    dom.statusText.textContent = "API Offline";
  }
}

// ── Scroll Reveal ─────────────────────────────────────────────────────────────
function setupScrollReveal() {
  const observer = new IntersectionObserver(
    (entries) => entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("revealed");
        observer.unobserve(e.target);
      }
    }),
    { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
  );
  document.querySelectorAll("[data-reveal]").forEach((el) => observer.observe(el));
}

// ── Init ─────────────────────────────────────────────────────────────────────
function init() {
  setupDragDrop();

  // Add data-reveal FIRST, then set up observer
  document.querySelectorAll(".step, .shape-card").forEach((el, i) => {
    el.setAttribute("data-reveal", "");
    el.style.transitionDelay = `${i * 80}ms`;
  });
  setupScrollReveal();

  // Gender buttons
  dom.genderMale.addEventListener("click", () => selectGender("male"));
  dom.genderFemale.addEventListener("click", () => selectGender("female"));

  // Lightbox close
  document.getElementById("lightboxClose").addEventListener("click", closeLightbox);
  document.getElementById("lightbox").addEventListener("click", (e) => {
    if (e.target === document.getElementById("lightbox")) closeLightbox();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeLightbox();
  });

  // Analyze button
  dom.btnAnalyze.addEventListener("click", runPrediction);

  // Clear history
  dom.btnClearHistory.addEventListener("click", clearHistory);

  // Health check on load + every 30s
  checkHealth();
  setInterval(checkHealth, 30_000);
}


// ── Scroll Fade Effect ────────────────────────────────────────────────────────
function setupScrollFade() {
  // .hero-bg is now directly in <body> (fixed), NOT inside .hero
  // so scroll fade only targets content sections
  const sections = document.querySelectorAll(
    ".hero, .how-section, .shapes-section"  // analyzer-section excluded — no fade on results
  );

  const onScroll = () => {
    const vh = window.innerHeight;

    sections.forEach((sec) => {
      const rect = sec.getBoundingClientRect();
      const center = rect.top + rect.height / 2;

      // Distance dari tengah viewport (0 = tepat di tengah)
      const distFromCenter = center - vh / 2;

      // Normalize: mulai fade saat section mulai keluar viewport
      const fadeZone = vh * 0.55;
      const ratio = Math.max(0, Math.min(1, 1 - Math.abs(distFromCenter) / fadeZone));

      // opacity 0.15 saat jauh, 1 saat di tengah
      const opacity = 0.15 + ratio * 0.85;

      // scale 0.97 saat jauh, 1 saat di tengah
      const scale = 0.97 + ratio * 0.03;

      sec.style.opacity = opacity;
      sec.style.transform = `scale(${scale})`;
      sec.style.transition = "opacity 0.15s ease, transform 0.15s ease";
    });
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll(); // run once on load
}

document.addEventListener("DOMContentLoaded", () => { init(); setupScrollFade(); });