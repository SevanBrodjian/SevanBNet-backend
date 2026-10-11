// The QR code manager inside the control panel (admin/qr_dashboard.html).
// Loaded with `defer`, so the page's markup is already there.
(() => {
  // Settings come from data attributes on #qr-app (see admin/qr_dashboard.html).
  const APP = document.getElementById('qr-app');
  const QR_BASE = APP.dataset.qrBase;
  const API_URL = APP.dataset.api;
  const IMAGE_URL = APP.dataset.image;

  // ── Utilities ─────────────────────────────────────────────────────────────
  function csrf() {
    return APP.dataset.csrf;
  }

  function esc(s) {
    return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;')
                          .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  function toast(msg, type = '') {
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = msg;
    document.getElementById('toast-container').appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3000);
  }

  // ── API ───────────────────────────────────────────────────────────────────
  const API = {
    async call(url, opts = {}) {
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
        ...opts,
      });
      if (res.status === 204) return null;
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
      return body;
    },
    list:   ()      => API.call(API_URL),
    create: (d)     => API.call(API_URL, { method: 'POST',   body: JSON.stringify(d) }),
    patch:  (id, d) => API.call(`${API_URL}${id}/`, { method: 'PATCH',  body: JSON.stringify(d) }),
    del:    (id)    => API.call(`${API_URL}${id}/`, { method: 'DELETE' }),
  };

  // ── Sparkline ─────────────────────────────────────────────────────────────
  function sparkline(days) {
    if (!days?.length) return '';
    const W = 168, H = 34, gap = 1;
    const bw  = Math.floor((W - gap * (days.length - 1)) / days.length);
    const max = Math.max(...days.map(d => d.count), 1);
    const bars = days.map((d, i) => {
      const bh = d.count === 0 ? 2 : Math.max(Math.round((d.count / max) * H), 3);
      return `<rect x="${i*(bw+gap)}" y="${H-bh}" width="${bw}" height="${bh}" rx="1"
                fill="var(--accent)" fill-opacity="${d.count ? .75 : .15}"/>`;
    }).join('');
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${bars}</svg>`;
  }

  // ── Image URL builder ─────────────────────────────────────────────────────
  function imgUrl(id, fg, bg, style, radius, transparent, download = false) {
    const p = new URLSearchParams({
      fg, bg, style,
      radius: parseFloat(radius).toFixed(2),
      transparent: transparent ? '1' : '0',
      t: Date.now(),
    });
    if (download) p.set('download', '1');
    return `${IMAGE_URL}${id}/?${p}`;
  }

  // ── Card HTML ─────────────────────────────────────────────────────────────
  function cardHTML(r) {
    const shortUrl = `${QR_BASE}/r/${r.short_code}/`;
    const created  = new Date(r.created_at).toLocaleDateString('en-US',
                     { year:'numeric', month:'short', day:'numeric' });
    const scanWord = r.total_scans === 1 ? 'scan' : 'scans';
    const radVal   = parseFloat(r.qr_radius).toFixed(2);

    return `
    <div class="card ${r.is_active ? '' : 'inactive'}" data-id="${r.id}">

      <div class="card-section card-header">
        <input class="label-input" value="${esc(r.label)}"
               data-orig="${esc(r.label)}" placeholder="Label" title="Click to edit label">
        <label class="toggle-switch" title="${r.is_active ? 'Active' : 'Inactive'}">
          <input type="checkbox" class="toggle-chk" ${r.is_active ? 'checked' : ''}>
          <span class="toggle-track"><span class="toggle-thumb"></span></span>
        </label>
      </div>

      <div class="card-section card-qr">
        <img class="qr-img" src="${IMAGE_URL}${r.id}/" alt="QR code" loading="lazy">
      </div>

      <div class="card-section">
        <div class="url-row">
          <span class="short-url-text" title="${esc(shortUrl)}">${esc(shortUrl)}</span>
          <button class="copy-btn" data-url="${esc(shortUrl)}">Copy</button>
        </div>
      </div>

      <div class="card-section">
        <div class="target-row">
          <input class="target-input" value="${esc(r.target_url)}"
                 data-orig="${esc(r.target_url)}" type="url" placeholder="Target URL">
          <button class="save-btn">Save</button>
        </div>
      </div>

      <div class="card-section">
        <div class="appearance-row">
          <select class="style-select">
            <option value="square"  ${r.qr_style==='square'  ?'selected':''}>Square</option>
            <option value="rounded" ${r.qr_style==='rounded' ?'selected':''}>Rounded</option>
            <option value="circle"  ${r.qr_style==='circle'  ?'selected':''}>Circle</option>
            <option value="gapped"  ${r.qr_style==='gapped'  ?'selected':''}>Gapped</option>
          </select>
          <input type="color" class="clr-fg" value="${esc(r.fg_color)}" title="Foreground">
          <input type="color" class="clr-bg" value="${esc(r.bg_color)}" title="Background">
          <label class="transp-label" title="Transparent background">
            <input type="checkbox" class="transp-chk" ${r.bg_transparent ? 'checked' : ''}>
            Transp
          </label>
        </div>
        <div class="radius-row ${r.qr_style !== 'rounded' ? 'hidden' : ''}">
          <span class="radius-label">Radius</span>
          <input type="range" class="radius-slider" min="0" max="1" step="0.05" value="${r.qr_radius}">
          <span class="radius-val">${radVal}</span>
        </div>
        <div class="apply-row">
          <button class="apply-btn">↻ Apply</button>
          <a class="dl-btn" href="${IMAGE_URL}${r.id}/?download=1" download="qr-${esc(r.short_code)}.png">⬇ PNG</a>
        </div>
      </div>

      <div class="card-section">
        <div class="stats-row">
          <div class="sparkline-wrap">
            ${sparkline(r.scans_14d)}
            <span class="spark-label">last 14 days</span>
          </div>
          <div>
            <div class="total-scans">${r.total_scans}</div>
            <div class="total-scans-sub">${scanWord} total</div>
          </div>
        </div>
      </div>

      <div class="card-section card-footer">
        <span class="created-date">Created ${created}</span>
        <button class="delete-btn">Delete</button>
      </div>
    </div>`;
  }

  // ── Bind card interactions ────────────────────────────────────────────────
  function bindCard(r) {
    const card = document.querySelector(`.card[data-id="${r.id}"]`);
    if (!card) return;

    // ── Active toggle
    card.querySelector('.toggle-chk').addEventListener('change', async function() {
      try {
        await API.patch(r.id, { is_active: this.checked });
        card.classList.toggle('inactive', !this.checked);
        this.closest('.toggle-switch').title = this.checked ? 'Active' : 'Inactive';
      } catch(e) {
        this.checked = !this.checked;
        toast(`Error: ${e.message}`, 'err');
      }
    });

    // ── Label
    const labelEl = card.querySelector('.label-input');
    const saveLabel = async () => {
      const v = labelEl.value.trim();
      if (!v || v === labelEl.dataset.orig) return;
      try { await API.patch(r.id, { label: v }); labelEl.dataset.orig = v; }
      catch(e) { labelEl.value = labelEl.dataset.orig; toast(`Error: ${e.message}`, 'err'); }
    };
    labelEl.addEventListener('blur', saveLabel);
    labelEl.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); labelEl.blur(); } });

    // ── Target URL
    const targetEl = card.querySelector('.target-input');
    const saveBtn  = card.querySelector('.save-btn');
    const saveTarget = async () => {
      const v = targetEl.value.trim();
      if (!v || v === targetEl.dataset.orig) return;
      try {
        saveBtn.textContent = '…';
        await API.patch(r.id, { target_url: v });
        targetEl.dataset.orig = v;
        saveBtn.textContent = '✓';
        setTimeout(() => saveBtn.textContent = 'Save', 1600);
      } catch(e) {
        targetEl.value = targetEl.dataset.orig; saveBtn.textContent = 'Save';
        toast(`Error: ${e.message}`, 'err');
      }
    };
    saveBtn.addEventListener('click', saveTarget);
    targetEl.addEventListener('keydown', e => { if (e.key === 'Enter') saveTarget(); });

    // ── Copy URL
    const copyBtn = card.querySelector('.copy-btn');
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(copyBtn.dataset.url).then(() => {
        copyBtn.textContent = 'Copied!';
        setTimeout(() => copyBtn.textContent = 'Copy', 2000);
      });
    });

    // ── Appearance controls + live preview
    const styleEl   = card.querySelector('.style-select');
    const fgEl      = card.querySelector('.clr-fg');
    const bgEl      = card.querySelector('.clr-bg');
    const transpEl  = card.querySelector('.transp-chk');
    const radiusEl  = card.querySelector('.radius-slider');
    const radiusVal = card.querySelector('.radius-val');
    const radiusRow = card.querySelector('.radius-row');
    const apBtn     = card.querySelector('.apply-btn');
    const qrImg     = card.querySelector('.qr-img');
    const dlBtn     = card.querySelector('.dl-btn');

    // Live preview — dims QR, loads new version in background, swaps when ready
    const livePreview = debounce(() => {
      const src = imgUrl(r.id, fgEl.value, bgEl.value,
                         styleEl.value, radiusEl.value, transpEl.checked);
      qrImg.style.opacity = '0.45';
      const tmp = new Image();
      tmp.onload = () => { qrImg.src = tmp.src; qrImg.style.opacity = '1'; };
      tmp.onerror = () => { qrImg.style.opacity = '1'; };
      tmp.src = src;
    }, 350);

    styleEl.addEventListener('change', () => {
      radiusRow.classList.toggle('hidden', styleEl.value !== 'rounded');
      livePreview();
    });
    fgEl.addEventListener('input',    livePreview);
    bgEl.addEventListener('input',    livePreview);
    transpEl.addEventListener('change', livePreview);
    radiusEl.addEventListener('input', () => {
      radiusVal.textContent = parseFloat(radiusEl.value).toFixed(2);
      livePreview();
    });

    // Apply — persists to DB and updates download link
    apBtn.addEventListener('click', async () => {
      try {
        apBtn.textContent = '…';
        await API.patch(r.id, {
          fg_color:       fgEl.value,
          bg_color:       bgEl.value,
          qr_style:       styleEl.value,
          qr_radius:      parseFloat(radiusEl.value),
          bg_transparent: transpEl.checked,
        });
        dlBtn.href = imgUrl(r.id, fgEl.value, bgEl.value,
                            styleEl.value, radiusEl.value, transpEl.checked, true);
        dlBtn.download = `qr-${r.short_code}.png`;
        apBtn.textContent = '↻ Apply';
        toast('Appearance saved', 'ok');
      } catch(e) {
        apBtn.textContent = '↻ Apply';
        toast(`Error: ${e.message}`, 'err');
      }
    });

    // ── Delete
    card.querySelector('.delete-btn').addEventListener('click', async () => {
      const note = r.total_scans ? ` and its ${r.total_scans} scan record${r.total_scans !== 1 ? 's' : ''}` : '';
      if (!confirm(`Delete "${r.label}"${note}? This cannot be undone.`)) return;
      try {
        await API.del(r.id);
        card.style.transition = 'opacity .25s, transform .25s';
        card.style.opacity = '0'; card.style.transform = 'scale(.96)';
        setTimeout(() => card.remove(), 280);
      } catch(e) { toast(`Error: ${e.message}`, 'err'); }
    });
  }

  // ── Render all cards ──────────────────────────────────────────────────────
  async function refresh() {
    const grid = document.getElementById('cards-grid');
    try {
      const data = await API.list();
      if (!data.length) {
        grid.innerHTML = '<div class="empty-state">No QR codes yet.</div>';
        return;
      }
      grid.innerHTML = data.map(cardHTML).join('');
      data.forEach(bindCard);
    } catch(e) {
      grid.innerHTML = `<div class="empty-state">Couldn't load the QR codes: ${esc(e.message)}</div>`;
    }
  }

  // ── New redirect form ─────────────────────────────────────────────────────
  function setupNewForm() {
    const panel  = document.getElementById('new-form-panel');
    const form   = document.getElementById('new-form');
    const newBtn = document.getElementById('new-btn');
    const canBtn = document.getElementById('cancel-btn');

    const open  = () => { panel.classList.add('open');    newBtn.textContent = 'Cancel'; };
    const close = () => { panel.classList.remove('open'); newBtn.textContent = 'New QR code'; form.reset(); updateFormRadius(); };

    newBtn.addEventListener('click', () => panel.classList.contains('open') ? close() : open());
    canBtn.addEventListener('click', close);

    // Show/hide radius row in new-form
    const fStyle  = form.qr_style;
    const fRGroup = document.getElementById('f-radius-group');
    const fRadius = document.getElementById('f-radius');
    const fRadVal = document.getElementById('f-radius-val');
    function updateFormRadius() {
      fRGroup.style.display = fStyle.value === 'rounded' ? '' : 'none';
    }
    fStyle.addEventListener('change', updateFormRadius);
    fRadius.addEventListener('input', () => {
      fRadVal.textContent = parseFloat(fRadius.value).toFixed(2);
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const sub = form.querySelector('[type="submit"]');
      sub.disabled = true; sub.textContent = 'Creating…';
      try {
        await API.create({
          label:          form.label.value.trim(),
          short_code:     form.short_code.value.trim(),
          target_url:     form.target_url.value.trim(),
          fg_color:       form.fg_color.value,
          bg_color:       form.bg_color.value,
          qr_style:       form.qr_style.value,
          qr_radius:      parseFloat(form.qr_radius.value),
          bg_transparent: form.bg_transparent.checked,
        });
        close();
        await refresh();
        toast('QR code created', 'ok');
      } catch(e) {
        toast(`Error: ${e.message}`, 'err');
      } finally {
        sub.disabled = false; sub.textContent = 'Create QR code';
      }
    });
  }

  // ── Boot ──────────────────────────────────────────────────────────────────
  setupNewForm();
  refresh();
})();
