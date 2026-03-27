/* ── ShazamSync — app.js ───────────────────────────────────── */

// Stato globale
const State = {
  step:       1,
  csvSongs:   [],
  localFiles: [],
  missing:    [],
  ambiguous:  [],
  matched:    [],
  selected:   new Set(),
  sessionId:  null,
  dlFolder:   "",
};

// ── Utilities ──────────────────────────────────────────────

function $(id) { return document.getElementById(id); }

function toast(msg, type = "") {
  const t = $("toast");
  t.textContent = msg;
  t.className   = `toast ${type}`;
  t.classList.remove("hidden");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add("hidden"), 3000);
}

function setStep(n) {
  State.step = n;
  for (let i = 1; i <= 4; i++) {
    const ind   = $(`step-ind-${i}`);
    const panel = $(`panel-${i}`);
    if (i < n)  { ind.className = "step done";   panel.classList.add("hidden"); }
    if (i === n){ ind.className = "step active";  panel.classList.remove("hidden"); }
    if (i > n)  { ind.className = "step";         panel.classList.add("hidden"); }
  }
  // Colora le linee tra step
  document.querySelectorAll(".step-line").forEach((el, idx) => {
    el.classList.toggle("done", idx + 1 < n);
  });
}

// ── STEP 1: CSV Upload ─────────────────────────────────────

const dropzone  = $("dropzone");
const csvInput  = $("csv-input");

dropzone.addEventListener("click", () => csvInput.click());
dropzone.addEventListener("dragover",  e => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", e => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file) uploadCSV(file);
});
csvInput.addEventListener("change", () => {
  if (csvInput.files[0]) uploadCSV(csvInput.files[0]);
});

async function uploadCSV(file) {
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res  = await fetch("/api/upload/csv", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) { toast(data.error || "Errore upload", "err"); return; }

    State.csvSongs = data.preview;  // per la preview
    renderCSVPreview(data.preview, data.total);
    $("btn-step1").disabled = false;
    toast(`${data.total} canzoni caricate`, "ok");
  } catch (e) {
    toast("Errore di rete", "err");
  }
}

function renderCSVPreview(songs, total) {
  $("csv-count").textContent = `${total} canzoni`;
  const tbody = $("csv-table").querySelector("tbody");
  tbody.innerHTML = songs.map((s, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${esc(s.title)}</td>
      <td>${esc(s.artist)}</td>
      <td style="color:var(--txt-m)">${s.date || "—"}</td>
    </tr>
  `).join("");
  $("csv-preview").classList.remove("hidden");
}

$("csv-remove").addEventListener("click", async () => {
  await fetch("/api/upload/csv", { method: "DELETE" });
  $("csv-preview").classList.add("hidden");
  $("btn-step1").disabled = true;
  csvInput.value = "";
  toast("CSV rimosso");
});

$("btn-step1").addEventListener("click", () => setStep(2));

// ── STEP 2: Folder ─────────────────────────────────────────

const folderPaths = [];

function renderFolderTags() {
  $("folder-tags").innerHTML = folderPaths.map((p, i) => `
    <div class="folder-tag">
      <span>${esc(p)}</span>
      <span class="remove" data-idx="${i}">&times;</span>
    </div>
  `).join("");
  $("folder-tags").querySelectorAll(".remove").forEach(el => {
    el.addEventListener("click", () => {
      folderPaths.splice(parseInt(el.dataset.idx), 1);
      renderFolderTags();
    });
  });
}

$("btn-browse").addEventListener("click", async () => {
  try {
    const res  = await fetch("/api/folder/browse");
    const data = await res.json();
    if (data.path) $("folder-path").value = data.path;
  } catch (e) {
    toast("Impossibile aprire il dialog", "err");
  }
});

$("btn-add-folder").addEventListener("click", () => {
  const path = $("folder-path").value.trim();
  if (!path) { toast("Inserisci un percorso", "err"); return; }
  if (folderPaths.includes(path)) { toast("Cartella già aggiunta", "err"); return; }
  folderPaths.push(path);
  renderFolderTags();
  $("folder-path").value = "";
});

$("btn-scan").addEventListener("click", async () => {
  // Se c'è un path nel campo ma non aggiunto, aggiungilo automaticamente
  const current = $("folder-path").value.trim();
  if (current && !folderPaths.includes(current)) {
    folderPaths.push(current);
    renderFolderTags();
    $("folder-path").value = "";
  }

  if (folderPaths.length === 0) { toast("Aggiungi almeno una cartella", "err"); return; }

  const res  = await fetch("/api/folder/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths: folderPaths }),
  });
  const data = await res.json();
  if (!res.ok) { toast(data.error, "err"); return; }

  $("folder-count").textContent = data.total;
  $("file-list").innerHTML = data.preview.map(f => `<div>${esc(f)}</div>`).join("") +
    (data.total > 10 ? `<div style="color:var(--txt-m)">… e altri ${data.total - 10}</div>` : "");
  $("folder-result").classList.remove("hidden");
  $("btn-step2").disabled = false;
  if (data.total === 0) {
    toast("Nessun file audio trovato — tutte le canzoni saranno mancanti", "ok");
  } else {
    toast(`${data.total} file trovati`, "ok");
  }
});

$("btn-back-1").addEventListener("click", () => setStep(1));
$("btn-step2").addEventListener("click", () => setStep(3));

// ── STEP 3: Match ───────────────────────────────────────────

$("threshold").addEventListener("input", () => {
  $("threshold-val").textContent = $("threshold").value;
});

$("btn-match").addEventListener("click", async () => {
  $("btn-match").disabled = true;
  $("btn-match").textContent = "Analisi in corso…";

  const threshold = parseInt($("threshold").value);
  const res  = await fetch("/api/match/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ threshold }),
  });
  const data = await res.json();
  $("btn-match").disabled = false;
  $("btn-match").textContent = "Esegui analisi";

  if (!res.ok) { toast(data.error, "err"); return; }

  State.missing   = data.missing;
  State.ambiguous = data.ambiguous;
  State.matched   = data.matched;
  State.selected  = new Set(data.missing.map((_, i) => `m-${i}`));

  $("count-matched").textContent   = data.stats.matched;
  $("count-missing").textContent   = data.stats.missing;
  $("count-ambiguous").textContent = data.stats.ambiguous;

  renderSongList("missing-list",   data.missing,   "m");
  renderSongList("ambiguous-list", data.ambiguous, "a");
  renderSongList("matched-list",   data.matched,   null);

  updateSelectedCount();
  $("match-results").classList.remove("hidden");
  $("btn-step3").disabled = State.selected.size === 0;
  toast("Analisi completata", "ok");
});

function renderSongList(containerId, songs, prefix) {
  const el = $(containerId);
  const checkable = prefix !== null;
  if (!songs.length) {
    el.innerHTML = `<div style="color:var(--txt-m);padding:12px">Nessuna canzone in questa categoria.</div>`;
    return;
  }
  el.innerHTML = songs.map((s, i) => {
    const key = `${prefix}-${i}`;
    const scoreClass = s.score >= 72 ? "score-ok" : "score-warn";
    const scoreTag   = s.score != null ? `<span class="song-score ${scoreClass}">${s.score}%</span>` : "";
    const cb = checkable
      ? `<input type="checkbox" data-key="${key}" ${State.selected.has(key) ? "checked" : ""}>`
      : "";
    return `
      <div class="song-item ${checkable && State.selected.has(key) ? "selected" : ""}" data-key="${key}">
        ${cb}
        <div style="flex:1;min-width:0">
          <div style="font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.title)}</div>
          <div class="song-artist">${esc(s.artist)}</div>
        </div>
        ${scoreTag}
      </div>`;
  }).join("");

  if (checkable) {
    el.querySelectorAll("input[type=checkbox]").forEach(cb => {
      cb.addEventListener("change", e => {
        const key = e.target.dataset.key;
        const item = e.target.closest(".song-item");
        if (e.target.checked) { State.selected.add(key); item.classList.add("selected"); }
        else                  { State.selected.delete(key); item.classList.remove("selected"); }
        updateSelectedCount();
        $("btn-step3").disabled = State.selected.size === 0;
      });
    });
  }
}

function updateSelectedCount() {
  $("selected-count").textContent = `${State.selected.size} selezionate`;
}

// Select all (missing + ambiguous)
$("select-all").addEventListener("change", e => {
  if (e.target.checked) {
    State.missing.forEach((_, i) => State.selected.add(`m-${i}`));
    State.ambiguous.forEach((_, i) => State.selected.add(`a-${i}`));
  } else {
    State.selected.clear();
  }
  renderSongList("missing-list", State.missing, "m");
  renderSongList("ambiguous-list", State.ambiguous, "a");
  updateSelectedCount();
  $("btn-step3").disabled = State.selected.size === 0;
});

// Tabs
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(tc => tc.classList.add("hidden"));
    tab.classList.add("active");
    $(`tab-${tab.dataset.tab}`).classList.remove("hidden");
  });
});

$("btn-back-2").addEventListener("click", () => setStep(2));

$("btn-step3").addEventListener("click", () => {
  const songs = [...State.selected].map(key => {
    const [prefix, idx] = key.split("-");
    return prefix === "m" ? State.missing[parseInt(idx)] : State.ambiguous[parseInt(idx)];
  });
  State._songsToDownload = songs;
  setStep(4);
  $("dl-total").textContent = songs.length;
  $("btn-start-dl").disabled = false;
  $("dl-progress-label").textContent = `Pronto — ${songs.length} canzoni da scaricare`;
});

$("btn-start-dl").addEventListener("click", () => {
  $("btn-start-dl").disabled = true;
  startDownload(State._songsToDownload);
});

// ── STEP 4: Download ────────────────────────────────────────

$("btn-dl-browse").addEventListener("click", async () => {
  const res  = await fetch("/api/folder/browse");
  const data = await res.json();
  if (data.path) $("dl-folder").value = data.path;
});

async function startDownload(songs) {
  const folder = $("dl-folder").value.trim() || null;
  const res    = await fetch("/api/download/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ songs, folder }),
  });
  const data = await res.json();
  if (!res.ok) { toast(data.error, "err"); return; }

  State.sessionId = data.session_id;
  State.dlFolder  = folder;
  listenSSE(data.session_id, songs.length);
}

// Download log tabs
document.querySelectorAll(".dl-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".dl-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    const target = tab.dataset.dlTab;
    $("log-box").classList.toggle("hidden", target !== "all");
    $("log-box-errors").classList.toggle("hidden", target !== "errors");
  });
});

function listenSSE(sessionId, total) {
  const src = new EventSource(`/api/download/stream/${sessionId}`);
  let done = 0, ok = 0, err = 0;

  const logBox    = $("log-box");
  const errBox    = $("log-box-errors");
  const errBadge  = $("err-badge");
  logBox.innerHTML = "";
  errBox.innerHTML = '<div style="color:var(--txt-m);padding:12px" id="no-errors-msg">Nessun errore per ora.</div>';
  errBadge.textContent = "0";
  errBadge.classList.add("hidden");

  function addLog(msg, cls) {
    const div = document.createElement("div");
    div.className = `log-item ${cls}`;
    div.textContent = msg;
    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
  }

  function addError(msg) {
    const noMsg = $("no-errors-msg");
    if (noMsg) noMsg.remove();
    const div = document.createElement("div");
    div.className = "log-item err";
    div.textContent = msg;
    errBox.appendChild(div);
    errBox.scrollTop = errBox.scrollHeight;
    errBadge.textContent = err;
    errBadge.classList.remove("hidden");
  }

  src.addEventListener("song_start", e => {
    const d = JSON.parse(e.data);
    $("current-song-name").textContent = d.song;
    $("current-song-box").classList.remove("hidden");
    $("song-progress-bar").style.width = "0%";
    addLog(`⟳  ${d.song}`, "spin");
    $("dl-progress-label").textContent = `Download ${d.index} di ${d.total}…`;
  });

  src.addEventListener("progress", e => {
    const d = JSON.parse(e.data);
    $("song-progress-bar").style.width = d.percent + "%";
  });

  src.addEventListener("song_ok", e => {
    const d = JSON.parse(e.data);
    done++; ok++;
    $("dl-done").textContent = done;
    $("dl-ok").textContent   = `${ok} ok`;
    $("dl-progress-bar").style.width = Math.round(done / total * 100) + "%";
    // Aggiorna ultima riga log
    const last = logBox.lastChild;
    if (last) { last.className = "log-item ok"; last.textContent = `✓  ${d.song}`; }
    $("song-progress-bar").style.width = "100%";
  });

  src.addEventListener("song_err", e => {
    const d = JSON.parse(e.data);
    done++; err++;
    $("dl-done").textContent  = done;
    $("dl-err").textContent   = `${err} errori`;
    $("dl-progress-bar").style.width = Math.round(done / total * 100) + "%";
    const last = logBox.lastChild;
    if (last) { last.className = "log-item err"; last.textContent = `✗  ${d.song}`; }
    addError(`✗  ${d.song}`);
  });

  src.addEventListener("done", e => {
    const d = JSON.parse(e.data);
    $("current-song-box").classList.add("hidden");
    $("dl-progress-label").textContent = `Completato! ${d.ok} scaricate, ${d.err} errori.`;
    $("dl-progress-bar").style.width = "100%";
    $("dl-footer").style.display = "flex";
    addLog(`── Fine: ${d.ok} ok, ${d.err} errori ──`, "wait");
    src.close();
    toast(`Download completato: ${d.ok} canzoni`, "ok");
  });

  src.addEventListener("cancelled", () => {
    $("dl-progress-label").textContent = "Download interrotto.";
    src.close();
  });

  src.addEventListener("stream_end", () => src.close());
  src.onerror = () => src.close();
}

$("btn-cancel").addEventListener("click", async () => {
  if (!State.sessionId) return;
  await fetch(`/api/download/cancel/${State.sessionId}`, { method: "POST" });
  toast("Stop richiesto…");
});

$("btn-open-folder").addEventListener("click", async () => {
  const folder = $("dl-folder").value.trim();
  if (folder) {
    // Usa l'API di sistema via backend (fallback: mostra path)
    toast(`Cartella: ${folder}`);
  }
});

$("btn-new-session").addEventListener("click", () => {
  location.reload();
});

// ── Helpers ─────────────────────────────────────────────────

function esc(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// Init
setStep(1);

// Precompila cartella di default
fetch("/api/folder/default").then(r => r.json()).then(data => {
  if (data.path) {
    $("folder-path").value = data.path;
    $("dl-folder").value   = data.path;
  }
});
