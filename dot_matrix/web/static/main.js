// Entry point: registers lazily loaded pages, sets the footer mode text, draws the background and starts the router.
import { start, lazy, route, app, isStatic, $ } from './core.js';

const PAGES = { 'home.js': ['home'], 'studio.js': ['studio'], 'gallery.js': ['gallery'], 'about.js': ['about'] };
lazy(Object.fromEntries(Object.entries(PAGES).flatMap(([file, names]) => names.map(n => [n, () => import('./' + file)]))));
route('notfound', () => { app().innerHTML = '<h1>Not found</h1><p><a href="#/">Back to the start</a></p>'; });

$('#mode').textContent = isStatic()
  ? 'static site: conversion runs in your browser (JS port); images are never uploaded'
  : 'local app: browser preview plus the real Python converter';

// Subtle background: a slowly breathing dot grid (off under prefers-reduced-motion).
(function background() {
  const cv = $('#bg'), ctx = cv.getContext('2d');
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const draw = t => {
    const w = cv.width = innerWidth, h = cv.height = innerHeight, s = 28;
    ctx.clearRect(0, 0, w, h);
    for (let y = s / 2; y < h; y += s) for (let x = s / 2; x < w; x += s) {
      const r = 1.2 + 2.2 * (0.5 + 0.5 * Math.sin(t / 2400 + x * 0.013 + y * 0.017));
      ctx.fillStyle = (Math.floor(x / s) + Math.floor(y / s)) % 7 ? 'rgba(255,176,0,.35)' : 'rgba(255,63,164,.45)';
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
    }
  };
  if (still) { draw(0); addEventListener('resize', () => draw(0)); return; }
  let last = 0;
  const loop = t => { if (t - last > 90) { draw(t); last = t; } requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
})();

start();
