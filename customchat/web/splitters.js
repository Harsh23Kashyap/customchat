/* Local layout preference only: never changes an app file or exported Nerd. */
(() => {
 'use strict';
 const layout = document.querySelector('.layout');
 const menu = document.getElementById('menu');
 const col = document.getElementById('col');
 if (!layout || !menu || !col) return;
 const key = 'cc_settings_columns_v1';
 const previewKey = 'cc_settings_preview_hidden';
 const toggle = document.createElement('button');
 toggle.type = 'button'; toggle.className = 'mini preview-toggle';
 const bar = document.querySelector('.modebar');
 if (bar) bar.append(toggle);
 let previewHidden = false;
 try { previewHidden = localStorage.getItem(previewKey) === '1'; } catch (_) {}
 function togglePreview() {
  document.body.classList.toggle('settings-preview-hidden', previewHidden);
  toggle.textContent = previewHidden ? 'Show chat preview' : 'Hide chat preview';
  toggle.setAttribute('aria-pressed', String(!previewHidden));
  toggle.setAttribute('aria-controls', 'pvbox');
 }
 togglePreview();
 toggle.addEventListener('click', () => {
  previewHidden = !previewHidden; togglePreview();
  try { localStorage.setItem(previewKey, previewHidden ? '1' : '0'); } catch (_) {}
  refresh();
 });
 const gap = 36;
 let saved = null, drag = null;
 try {
  const value = JSON.parse(localStorage.getItem(key));
  if (value && Number.isFinite(value.nav) && Number.isFinite(value.right)) saved = value;
 } catch (_) { /* Unavailable or malformed storage must not block settings. */ }
 const handles = ['Navigation and settings', 'Settings and preview or editor'].map((label, i) => {
  const handle = document.createElement('div');
  handle.className = 'column-splitter';
  handle.tabIndex = 0;
  handle.setAttribute('role', 'separator');
  handle.setAttribute('aria-orientation', 'vertical');
  handle.setAttribute('aria-label', label + ' divider');
  handle.title = 'Drag to resize. Arrow keys adjust. Double-click or Home resets.';
  handle.innerHTML = '<span class="splitter-grip" aria-hidden="true"></span>';
  layout.append(handle);
  handle.addEventListener('pointerdown', e => {
   if (e.button !== 0 || !enabled()) return;
   e.preventDefault();
   handle.focus({preventScroll:true});
   drag = {i, id:e.pointerId, x:e.clientX, widths:widths()};
   handle.setPointerCapture(e.pointerId);
   document.body.classList.add('resizing-columns');
  });
  handle.addEventListener('pointermove', e => {
   if (!drag || drag.id !== e.pointerId) return;
   const delta = e.clientX - drag.x;
   apply(drag.widths.nav + (i === 0 ? delta : 0), drag.widths.right - (i === 1 ? delta : 0));
  });
  function finish(e) {
   if (!drag || drag.id !== e.pointerId) return;
   drag = null;
   document.body.classList.remove('resizing-columns');
   persist();
  }
  handle.addEventListener('pointerup', finish);
  handle.addEventListener('pointercancel', finish);
  handle.addEventListener('lostpointercapture', finish);
  handle.addEventListener('dblclick', reset);
  handle.addEventListener('keydown', e => {
   if (!enabled()) return;
   if (e.key === 'Home') { e.preventDefault(); reset(); return; }
   if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
   e.preventDefault();
   const w = widths(), delta = (e.key === 'ArrowRight' ? 1 : -1) * (e.shiftKey ? 40 : 10);
   apply(w.nav + (i === 0 ? delta : 0), w.right - (i === 1 ? delta : 0));
   persist();
  });
  return handle;
 });
 function enabled() {
  return matchMedia('(min-width:1181px)').matches &&
   !document.body.classList.contains('loading-nerd') &&
   !document.querySelector('#nerdReview .import-grid');
 }
 function widths() {
  return {nav:menu.getBoundingClientRect().width,
   right:(previewHidden && !document.body.classList.contains('prompt-pane-active')) ? parseFloat(layout.style.getPropertyValue('--settings-right-width')) || 560 : layout.clientWidth - menu.getBoundingClientRect().width - col.getBoundingClientRect().width - 2 * gap};
 }
 function limits(nav, right) {
  const available = layout.clientWidth - 2 * gap;
  // Keep every column usable, including at the smallest desktop breakpoint.
  const minRight = Math.min(300, Math.max(240, available - 140 - 320));
  nav = Math.max(140, Math.min(320, available - minRight - 320, nav));
  right = Math.max(minRight, Math.min(available - nav - 320, right));
  return {nav, right};
 }
 function position() {
  handles.forEach((h,i) => { h.hidden = !enabled() || (i === 1 && previewHidden && !document.body.classList.contains('prompt-pane-active')); });
  if (!enabled()) return;
  const w = widths(), middle = col.getBoundingClientRect().width;
  [w.nav + gap / 2, w.nav + gap + middle + gap / 2].forEach((x, i) => {
   handles[i].style.left = (x - 12) + 'px';
   const value = Math.round(i === 0 ? w.nav : middle);
   handles[i].setAttribute('aria-valuenow', value);
   handles[i].setAttribute('aria-valuetext', value + ' pixels');
   handles[i].setAttribute('aria-valuemin', i === 0 ? 140 : 320);
   handles[i].setAttribute('aria-valuemax', Math.round(i === 0 ? Math.min(320,layout.clientWidth-692) : layout.clientWidth-w.nav-372));
  });
 }
 function apply(nav, right) {
  const w = limits(nav, right);
  layout.style.setProperty('--settings-nav-width', w.nav + 'px');
  layout.style.setProperty('--settings-right-width', w.right + 'px');
  layout.classList.add('resizable-columns');
  position();
 }
 function persist() {
  saved = widths();
  try { localStorage.setItem(key, JSON.stringify(saved)); } catch (_) {}
 }
 function reset() {
  saved = null;
  layout.classList.remove('resizable-columns');
  layout.style.removeProperty('--settings-nav-width');
  layout.style.removeProperty('--settings-right-width');
  try { localStorage.removeItem(key); } catch (_) {}
  position();
 }
 function refresh() {
  if (enabled() && saved && !drag) apply(saved.nav, saved.right);
  position();
 }
 new ResizeObserver(refresh).observe(layout);
 new MutationObserver(refresh).observe(document.body, {attributes:true,attributeFilter:['class']});
 const review = document.getElementById('nerdReview');
 if (review) new MutationObserver(refresh).observe(review, {childList:true});
 window.addEventListener('resize', refresh);
 refresh();
})();
