/* ─────────────────────────────────────
   TruthLens — main.js
   Frontend interactivity
─────────────────────────────────────── */

// ── Navbar mobile toggle ──────────────
const navToggle = document.getElementById('navToggle');
const navLinks  = document.querySelector('.nav-links');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
  });
}

// ── Navbar scroll shrink ──────────────
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.style.background = window.scrollY > 20
      ? 'rgba(9,12,20,0.95)'
      : 'rgba(14,17,27,0.85)';
  });
}

// ── Input tabs ────────────────────────
const tabBtns   = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-panel');
const sourceType = document.getElementById('sourceType');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    tabBtns.forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected','false'); });
    tabPanels.forEach(p => p.classList.add('hidden'));
    btn.classList.add('active');
    btn.setAttribute('aria-selected','true');
    const panel = document.getElementById('panel-' + target);
    if (panel) panel.classList.remove('hidden');
    if (sourceType) sourceType.value = target;
    // Clear inputs from other tabs to avoid conflict
    clearOtherInputs(target);
  });
});

function clearOtherInputs(active) {
  if (active !== 'text') {
    const ta = document.getElementById('articleText');
    if (ta) ta.value = '';
  }
  if (active !== 'url') {
    const ui = document.getElementById('articleUrl');
    if (ui) ui.value = '';
  }
}

// ── Character counter ─────────────────
const textarea  = document.getElementById('articleText');
const charCount = document.getElementById('charCount');
const charWarn  = document.getElementById('charWarning');

if (textarea && charCount) {
  textarea.addEventListener('input', updateCharCount);
  updateCharCount();
}

function updateCharCount() {
  const len = textarea.value.length;
  charCount.textContent = len.toLocaleString();
  if (charWarn) {
    if (len < 50 && len > 0) {
      charWarn.textContent = `(need at least ${50 - len} more)`;
      charWarn.classList.remove('hidden');
    } else if (len >= 9000) {
      charWarn.textContent = `(${10000 - len} remaining)`;
      charWarn.classList.remove('hidden');
    } else {
      charWarn.classList.add('hidden');
    }
  }
}

// ── File drag-and-drop ────────────────
const dropZone  = document.getElementById('fileDropZone');
const fileInput = document.getElementById('fileInput');
const fileName  = document.getElementById('fileName');

if (dropZone && fileInput) {
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length) { fileInput.files = files; showFileName(files[0].name); }
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) showFileName(fileInput.files[0].name);
  });
}

function showFileName(name) {
  if (fileName) {
    fileName.textContent = '📄 ' + name;
    fileName.classList.remove('hidden');
  }
}

// ── Form submission loader ────────────
const detectForm = document.getElementById('detectForm');
const submitBtn  = document.getElementById('submitBtn');

if (detectForm && submitBtn) {
  detectForm.addEventListener('submit', (e) => {
    // Validate before submit
    const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab;
    if (activeTab === 'text') {
      const text = textarea?.value.trim() || '';
      if (text.length < 50) {
        e.preventDefault();
        textarea.focus();
        showFlash('warning', 'Please enter at least 50 characters of text.');
        return;
      }
    }
    if (activeTab === 'url') {
      const url = document.getElementById('articleUrl')?.value.trim() || '';
      if (!url.startsWith('http')) {
        e.preventDefault();
        showFlash('warning', 'Please enter a valid URL starting with http:// or https://');
        return;
      }
    }
    // Show loader
    const btnText   = submitBtn.querySelector('.btn-text');
    const btnIcon   = submitBtn.querySelector('.btn-icon');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    if (btnText)   btnText.classList.add('hidden');
    if (btnIcon)   btnIcon.classList.add('hidden');
    if (btnLoader) btnLoader.classList.remove('hidden');
    submitBtn.disabled = true;
  });
}

// ── Inline flash helper ───────────────
function showFlash(type, message) {
  const container = document.querySelector('.flash-container') || (() => {
    const c = document.createElement('div');
    c.className = 'flash-container';
    document.body.appendChild(c);
    return c;
  })();
  const flash = document.createElement('div');
  flash.className = `flash flash-${type}`;
  flash.innerHTML = `<span>${message}</span><button class="flash-close" onclick="this.parentElement.remove()">×</button>`;
  container.appendChild(flash);
  setTimeout(() => flash.remove(), 5000);
}

// ── Score colour helper (used in Jinja template) ──────────────────
window.scoreColor = function(score) {
  if (score >= 0.8) return '#22c55e';
  if (score >= 0.6) return '#86efac';
  if (score >= 0.4) return '#facc15';
  if (score >= 0.2) return '#f97316';
  return '#ef4444';
};

// ── Auto-dismiss flashes after 6s ────
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => el.remove(), 6000);
});
