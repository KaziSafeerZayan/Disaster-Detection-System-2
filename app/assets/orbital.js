/* Orthographic globe, drawn locally without WebGL or a remote animation library.
   Coastlines: Natural Earth 1:110m land (public domain). Satellite orbit is illustrative. */
window.mountFlooderOrbital = (navigation, reducedMotion) => {
  const land = __FLOODER_LAND__;
  const element = document.createElement('figure');
  element.className = 'orbital-visual';
  element.innerHTML = `<div class="orbital-label"><span>Orbital perspective</span>
    <button type="button" aria-label="Pause globe animation" title="Pause globe animation">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" aria-hidden="true"><path d="M6 4v8m4-8v8"/></svg>
    </button></div><canvas aria-hidden="true"></canvas>
    <figcaption><span class="orbital-key"></span>Simulated satellite orbit</figcaption>`;
  navigation.appendChild(element);
  const canvas = element.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const button = element.querySelector('button');
  if (!ctx) { element.remove(); return { element, destroy() {} }; }
  const events = new AbortController();
  const compact = window.matchMedia('(max-width: 760px), (max-height: 620px)');
  const radians = Math.PI / 180;
  const toPoint = ([lon, lat]) => {
    const a = lon * radians, b = lat * radians;
    return [Math.cos(b) * Math.sin(a), Math.sin(b), Math.cos(b) * Math.cos(a)];
  };
  const coastlines = land.map(ring => ring.map(toPoint));
  const graticules = [];
  for (let lat = -60; lat <= 60; lat += 30) {
    graticules.push(Array.from({ length: 121 }, (_, i) => toPoint([-180 + i * 3, lat])));
  }
  for (let lon = 0; lon < 360; lon += 30) {
    graticules.push(Array.from({ length: 61 }, (_, i) => toPoint([lon, -90 + i * 3])));
  }
  // Sample land once, so dense point geometry never needs spatial queries per frame.
  const bounds = land.map(ring => [
    Math.min(...ring.map(p => p[0])), Math.min(...ring.map(p => p[1])),
    Math.max(...ring.map(p => p[0])), Math.max(...ring.map(p => p[1]))
  ]);
  const inside = (x, y, ring) => {
    let hit = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [ax, ay] = ring[i], [bx, by] = ring[j];
      if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) hit = !hit;
    }
    return hit;
  };
  const dots = [];
  for (let lat = -75; lat <= 80; lat += 3.4) {
    const step = 3.4 / Math.max(.35, Math.cos(lat * radians));
    for (let lon = -180; lon < 180; lon += step) {
      if (land.some((ring, i) => {
        const [w, s, e, n] = bounds[i];
        return lon >= w && lon <= e && lat >= s && lat <= n && inside(lon, lat, ring);
      })) dots.push(toPoint([lon, lat]));
    }
  }
  let frame = null, destroyed = false, paused = false, elapsed = 0, last = null;
  let size = 0, theme = '', colors = {}, rendered = 0;
  function syncSize() {
    const width = canvas.clientWidth;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    if (size !== width || canvas.width !== Math.round(width * ratio)) {
      size = width;
      canvas.width = Math.round(size * ratio);
      canvas.height = Math.round(size * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }
    const currentTheme = document.documentElement.dataset.flooderTheme || 'dark';
    if (currentTheme !== theme) {
      theme = currentTheme;
      const light = theme === 'light';
      colors = { ink: light ? '40,106,119' : '103,217,231',
        ocean: light ? ['#e2e8e3', '#bccbd0', '#d1d6ce'] : ['#18333f', '#0d1c2b', '#080e18'],
        satellite: light ? '#2d6170' : '#dafbff' };
    }
  }
  function draw() {
    syncSize();
    if (size < 1) return;
    const center = size / 2, radius = size * .335;
    ctx.clearRect(0, 0, size, size);
    ctx.save();
    ctx.translate(center, center);
    const rotation = -1.35 + elapsed * .045;
    const cos = Math.cos(rotation), sin = Math.sin(rotation);
    const tilt = .23, ct = Math.cos(tilt), st = Math.sin(tilt);
    const project = point => {
      const x = point[0] * cos + point[2] * sin;
      const z = point[2] * cos - point[0] * sin;
      return [x * radius, -(point[1] * ct - z * st) * radius, z * ct + point[1] * st];
    };
    const color = alpha => `rgba(${colors.ink},${alpha})`;
    const orbit = angle => {
      const x = Math.cos(angle) * radius * 1.3;
      const y = Math.sin(angle) * radius * .5;
      const bank = -.55;
      return [x * Math.cos(bank) - y * Math.sin(bank),
        x * Math.sin(bank) + y * Math.cos(bank), Math.sin(angle)];
    };
    function orbitalPath(front) {
      ctx.beginPath();
      let pen = false;
      for (let i = 0; i <= 160; i++) {
        const p = orbit(i / 160 * Math.PI * 2);
        if ((p[2] >= 0) === front) {
          if (pen) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]);
          pen = true;
        } else pen = false;
      }
      ctx.strokeStyle = color(front ? .45 : .14);
      ctx.lineWidth = .65;
      ctx.setLineDash(front ? [] : [2, 4]);
      ctx.stroke(); ctx.setLineDash([]);
    }
    function satellite(p, angle) {
      const next = orbit(angle + .01);
      ctx.save();
      ctx.translate(p[0], p[1]);
      ctx.rotate(Math.atan2(next[1] - p[1], next[0] - p[0]));
      ctx.shadowColor = color(.6); ctx.shadowBlur = 8;
      ctx.strokeStyle = colors.satellite; ctx.fillStyle = color(.5); ctx.lineWidth = .75;
      ctx.fillRect(-2.2, -2.8, 4.4, 5.6); ctx.strokeRect(-2.2, -2.8, 4.4, 5.6);
      ctx.shadowBlur = 0;
      ctx.fillStyle = color(.15);
      ctx.fillRect(-3.3, -10, 6.6, 5.2); ctx.strokeRect(-3.3, -10, 6.6, 5.2);
      ctx.fillRect(-3.3, 4.8, 6.6, 5.2); ctx.strokeRect(-3.3, 4.8, 6.6, 5.2);
      ctx.beginPath(); ctx.moveTo(0, -4.8); ctx.lineTo(0, -2.8);
      ctx.moveTo(0, 2.8); ctx.lineTo(0, 4.8); ctx.moveTo(2.2, 0); ctx.lineTo(5.5, 0); ctx.stroke();
      ctx.restore();
    }
    const angle = elapsed * .28 + .85;
    const position = orbit(angle);
    orbitalPath(false);
    if (position[2] < 0) satellite(position, angle);
    const atmosphere = ctx.createRadialGradient(0, 0, radius * .9, 0, 0, radius * 1.18);
    atmosphere.addColorStop(0, color(0)); atmosphere.addColorStop(.42, color(.13)); atmosphere.addColorStop(1, color(0));
    ctx.fillStyle = atmosphere; ctx.beginPath(); ctx.arc(0, 0, radius * 1.18, 0, Math.PI * 2); ctx.fill();
    const sphere = ctx.createRadialGradient(-radius * .4, -radius * .45, 0, radius * .2, radius * .15, radius * 1.2);
    colors.ocean.forEach((c, i) => sphere.addColorStop(i / 2, c));
    ctx.fillStyle = sphere; ctx.beginPath(); ctx.arc(0, 0, radius, 0, Math.PI * 2); ctx.fill();
    function lines(paths, opacity, width) {
      ctx.beginPath();
      for (const path of paths) {
        let pen = false;
        for (const point of path) {
          const p = project(point);
          if (p[2] > .01) {
            if (pen) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]);
            pen = true;
          } else pen = false;
        }
      }
      ctx.strokeStyle = color(opacity); ctx.lineWidth = width; ctx.stroke();
    }
    lines(graticules, .17, .5);
    lines(coastlines, .56, .65);
    ctx.fillStyle = color(.48);
    ctx.beginPath();
    for (const point of dots) {
      const p = project(point);
      if (p[2] > .03) { ctx.moveTo(p[0] + .65, p[1]); ctx.arc(p[0], p[1], .65, 0, Math.PI * 2); }
    }
    ctx.fill();
    ctx.strokeStyle = color(.35); ctx.lineWidth = .6;
    ctx.beginPath(); ctx.arc(0, 0, radius, 0, Math.PI * 2); ctx.stroke();
    orbitalPath(true);
    if (position[2] >= 0) {
      const distance = Math.hypot(position[0], position[1]);
      const target = Math.min(radius * .88 / distance, .72);
      ctx.beginPath(); ctx.moveTo(position[0], position[1]);
      ctx.lineTo(position[0] * target - 6, position[1] * target);
      ctx.lineTo(position[0] * target + 6, position[1] * target + 4); ctx.closePath();
      ctx.fillStyle = color(.06); ctx.fill();
      satellite(position, angle);
    }
    // Fixed reticle belongs to the visualization, not to a live telemetry feed.
    ctx.strokeStyle = color(.25); ctx.lineWidth = .5;
    [-1, 1].forEach(sign => {
      ctx.beginPath(); ctx.moveTo(sign * radius * 1.39, -3); ctx.lineTo(sign * radius * 1.39, 3); ctx.stroke();
    });
    ctx.restore();
    rendered++;
    // A low-frequency DOM marker makes the motion's state inspectable without per-frame mutations.
    if (rendered % 60 === 1) canvas.dataset.orbitPosition = angle.toFixed(2);
  }
  function loop(now) {
    frame = null;
    if (destroyed || paused || reducedMotion.matches || compact.matches || document.hidden) { last = null; return; }
    if (last === null || now - last >= 32) {
      if (last !== null) elapsed += Math.min((now - last) / 1000, .1);
      last = now; draw();
    }
    frame = requestAnimationFrame(loop);
  }
  function refresh() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null; last = null;
    button.disabled = reducedMotion.matches;
    const staticMotion = paused || reducedMotion.matches;
    element.dataset.motion = staticMotion ? 'paused' : 'running';
    button.setAttribute('aria-label', paused ? 'Play globe animation' : 'Pause globe animation');
    button.title = reducedMotion.matches ? 'Reduced motion enabled' : button.getAttribute('aria-label');
    button.innerHTML = paused
      ? '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" aria-hidden="true"><path d="m6 4 6 4-6 4z"/></svg>'
      : '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" aria-hidden="true"><path d="M6 4v8m4-8v8"/></svg>';
    draw();
    if (!staticMotion && !compact.matches && !document.hidden) frame = requestAnimationFrame(loop);
  }
  button.addEventListener('click', () => { paused = !paused; refresh(); }, { signal: events.signal });
  document.addEventListener('visibilitychange', refresh, { signal: events.signal });
  reducedMotion.addEventListener('change', refresh, { signal: events.signal });
  compact.addEventListener('change', refresh, { signal: events.signal });
  window.addEventListener('resize', refresh, { signal: events.signal });
  const themeObserver = new MutationObserver(() => { if (paused || reducedMotion.matches) draw(); });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-flooder-theme'] });
  refresh();
  return { element, destroy() { destroyed = true; cancelAnimationFrame(frame); events.abort(); themeObserver.disconnect(); element.remove(); } };
};
