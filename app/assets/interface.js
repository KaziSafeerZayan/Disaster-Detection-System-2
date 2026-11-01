(() => {
  const version = 5;
  if (window.flooderInterface?.version === version) {
    window.flooderInterface.refresh();
    return;
  }
  window.flooderInterface?.destroy?.();
  const root = document.documentElement;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const events = new AbortController();
  let scheduled = false;
  let motion = null;
  let boot = null;
  let orbital = null;

  const loaderMarkup = `
    <div class="boot-visual" aria-hidden="true">
      <div class="boot-aura"></div>
      <svg class="boot-radar" viewBox="0 0 200 200" fill="none">
        <defs>
          <linearGradient id="boot-orbit-gradient"><stop stop-color="currentColor" stop-opacity="0"/><stop offset="1" stop-color="currentColor"/></linearGradient>
        </defs>
        <circle class="boot-ring-outer" cx="100" cy="100" r="86"/>
        <circle class="boot-ring-inner" cx="100" cy="100" r="66"/>
        <path class="boot-reticle" d="M100 8v10m0 164v10M8 100h10m164 0h10M40 40l7 7m106 106 7 7M40 160l7-7m106-106 7-7"/>
        <g class="boot-orbit"><circle cx="100" cy="100" r="76" pathLength="100"/><circle class="boot-orbit-point" cx="176" cy="100" r="2.5"/></g>
        <g class="boot-satellite">
          <path class="boot-satellite-body" d="m91 82 27 15-15 26-27-15z"/>
          <path d="m81 89-20-12-12 20 20 12m42-5 20 12 12-20-20-12M57 86l20 12m42-3 20 12M93 82l5-9m6 50-5 9"/>
          <path class="boot-beam boot-beam-one" d="M93 135q-16 0-24-12"/>
          <path class="boot-beam boot-beam-two" d="M95 145q-24 0-36-18"/>
        </g>
      </svg>
    </div>
    <div class="boot-copy">
      <p class="boot-kicker">Workspace initialization</p>
      <p class="boot-title">Satellite Assisted<br>Flood Detection System</p>
      <div class="boot-progress" aria-hidden="true"><span></span></div>
      <p class="boot-status">Preparing interface</p>
      <div class="boot-stages" aria-hidden="true">
        <span data-boot-stage="0"><i></i>Interface</span>
        <span data-boot-stage="1"><i></i>Map view</span>
        <span data-boot-stage="2"><i></i>Workspace</span>
      </div>
    </div>`;

  function setStyle(element, name, value) {
    if (element && element.style.getPropertyValue(name) !== value) element.style.setProperty(name, value);
  }

  function startLoading() {
    if (boot) return;
    const overlay = document.createElement('div');
    overlay.id = 'flooder-loader';
    overlay.setAttribute('role', 'status');
    overlay.setAttribute('aria-live', 'polite');
    overlay.setAttribute('aria-label', 'Loading Satellite Assisted Flood Detection System');
    overlay.innerHTML = loaderMarkup;
    document.body.appendChild(overlay);
    root.classList.add('flooder-booting');
    boot = { overlay, started: performance.now(), closing: false, readySince: null, timer: null };
    // A broken provider or script must never strand the user behind the loader.
    boot.timer = setTimeout(finishLoading, 30000);
    schedule();
  }

  function finishLoading() {
    if (!boot || boot.closing) return;
    boot.closing = true;
    clearTimeout(boot.timer);
    const overlay = boot.overlay;
    overlay.dataset.state = 'ready';
    overlay.querySelector('.boot-status').textContent = 'Opening workspace';
    overlay.querySelectorAll('[data-boot-stage]').forEach(stage => stage.dataset.ready = 'true');
    const content = document.querySelector('[data-testid="stMainBlockContainer"]');
    const duration = reducedMotion.matches ? 100 : 680;
    if (content && !reducedMotion.matches) {
      content.animate([
        { opacity: 0, transform: 'translateY(14px)', filter: 'blur(3px)' },
        { opacity: 1, transform: 'translateY(0)', filter: 'blur(0)' }
      ], { duration: 920, delay: 90, easing: 'cubic-bezier(.16,1,.3,1)' });
    }
    const exit = overlay.animate([
      { opacity: 1, transform: 'scale(1)', filter: 'blur(0)' },
      { opacity: 0, transform: 'scale(1.035)', filter: 'blur(5px)' }
    ], { duration, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards' });
    exit.finished.catch(() => {}).finally(() => {
      overlay.remove();
      root.classList.remove('flooder-booting');
      const app = document.querySelector('[data-testid="stApp"]');
      if (app) app.inert = false;
      boot = null;
      schedule();
    });
  }

  function updateLoading(app) {
    if (!boot || boot.closing) return;
    if (!app.inert) app.inert = true;
    const done = app.getAttribute('data-test-script-state') === 'notRunning';
    const failed = !!document.querySelector('[data-testid="stException"]');
    const interfaceReady = !!document.querySelector('h1, h2');
    const frames = [...document.querySelectorAll('iframe')];
    const mapReady = frames.every(frame => {
      try { return !!frame.contentDocument?.body?.childElementCount; } catch (_) { return true; }
    });
    const states = [interfaceReady, done && mapReady, done];
    boot.overlay.querySelectorAll('[data-boot-stage]').forEach((stage, index) => {
      const value = String(states[index]);
      if (stage.dataset.ready !== value) stage.dataset.ready = value;
    });
    const status = boot.overlay.querySelector('.boot-status');
    const copy = !interfaceReady ? 'Preparing interface' : !done ? 'Preparing flood analytics' : !mapReady ? 'Opening map view' : 'Workspace ready';
    if (status.textContent !== copy) status.textContent = copy;
    if (done || failed) {
      if (boot.readySince === null) boot.readySince = performance.now();
      const minimum = reducedMotion.matches ? 250 : 1600;
      const remaining = Math.max(0, minimum - (performance.now() - boot.started));
      if (mapReady || failed || performance.now() - boot.readySince > 3000) {
        clearTimeout(boot.timer);
        boot.timer = setTimeout(finishLoading, remaining);
      } else {
        setTimeout(schedule, 160);
      }
    }
  }

  function attachReload() {
    const menu = document.querySelector('[data-testid="stMainMenuList"]');
    if (!menu || menu.querySelector('[data-flooder-reload]')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'flooder-reload-item';
    button.dataset.flooderReload = 'true';
    button.setAttribute('role', 'menuitem');
    button.tabIndex = -1;
    button.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M20 7v5h-5M20 12a8 8 0 1 0-2 5M20 12l-4-5"/></svg><span>Reload site</span>';
    menu.insertBefore(button, menu.querySelector('[data-testid="stMainMenuItem-rerun"]'));
  }

  function update() {
    scheduled = false;
    const app = document.querySelector('[data-testid="stApp"]');
    if (!app) return;
    const channels = getComputedStyle(app).backgroundColor.match(/[\d.]+/g);
    if (channels?.length >= 3) {
      const lightness = .2126 * +channels[0] + .7152 * +channels[1] + .0722 * +channels[2];
      const theme = lightness > 140 ? 'light' : 'dark';
      if (root.dataset.flooderTheme !== theme) root.dataset.flooderTheme = theme;
      document.querySelectorAll('iframe').forEach(frame => {
        try {
          const frameRoot = frame.contentDocument?.documentElement;
          if (frameRoot && frameRoot.dataset.flooderTheme !== theme) frameRoot.dataset.flooderTheme = theme;
        } catch (_) { /* External frames retain their own theme. */ }
      });
    }
    attachReload();
    updateLoading(app);
    const links = [...document.querySelectorAll('.phase-link')];
    let active = links[0];
    links.forEach(link => {
      const heading = document.getElementById(link.hash.slice(1));
      if (heading && heading.getBoundingClientRect().top < window.innerHeight * .4) active = link;
    });
    const scroller = document.querySelector('[data-testid="stMain"]');
    if (scroller && scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 4) active = links.at(-1);
    if (motion) active = links.find(link => link.hash === motion.hash) || active;
    links.forEach(link => {
      if (link === active && link.getAttribute('aria-current') !== 'location') link.setAttribute('aria-current', 'location');
      else if (link !== active && link.hasAttribute('aria-current')) link.removeAttribute('aria-current');
    });
    const nav = document.querySelector('.phase-navigation');
    if (nav && (!orbital || !orbital.element.isConnected)) {
      orbital?.destroy();
      orbital = window.mountFlooderOrbital(nav, reducedMotion);
    } else if (!nav && orbital) {
      orbital.destroy();
      orbital = null;
    }
    if (active && nav) {
      setStyle(nav, '--nav-active-y', `${active.offsetTop}px`);
      setStyle(nav, '--nav-active-height', `${active.offsetHeight}px`);
    }
  }

  function schedule() {
    if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
  }

  function cancelMotion() {
    if (!motion) return;
    cancelAnimationFrame(motion.frame);
    clearTimeout(motion.revealTimer);
    motion.animations.forEach(animation => animation.cancel());
    motion.scroller.style.scrollBehavior = motion.previousBehavior;
    motion = null;
    delete root.dataset.phaseTransition;
    schedule();
  }

  function goToPhase(link) {
    const heading = document.getElementById(link.hash.slice(1));
    const scroller = document.querySelector('[data-testid="stMain"]');
    if (!heading || !scroller) return;
    cancelMotion();
    const start = scroller.scrollTop;
    const target = Math.max(0, Math.min(scroller.scrollHeight - scroller.clientHeight,
      start + heading.getBoundingClientRect().top - scroller.getBoundingClientRect().top - 28));
    history.replaceState(null, '', link.hash);
    if (reducedMotion.matches || Math.abs(target - start) < 3) {
      scroller.scrollTo({ top: target, behavior: 'instant' });
      schedule();
      return;
    }
    const duration = Math.min(1120, 740 + Math.abs(target - start) * .12);
    const began = performance.now();
    const transition = {
      scroller, hash: link.hash, previousBehavior: scroller.style.scrollBehavior,
      frame: null, revealTimer: null, animations: []
    };
    motion = transition;
    scroller.style.scrollBehavior = 'auto';
    root.dataset.phaseTransition = 'running';
    const section = heading.closest('[class*="st-key-phase-"]');
    transition.revealTimer = setTimeout(() => {
      const block = section?.matches('[data-testid="stVerticalBlock"]')
        ? section : section?.querySelector('[data-testid="stVerticalBlock"]');
      const elements = block ? [...block.children].slice(0, 10) : [heading];
      [...new Set(elements)].forEach((element, index) => {
        transition.animations.push(element.animate([
          { opacity: .25, transform: 'translateY(16px)', filter: 'blur(2px)' },
          { opacity: 1, transform: 'translateY(0)', filter: 'blur(0)' }
        ], { duration: 720, delay: index * 38, easing: 'cubic-bezier(.16,1,.3,1)' }));
      });
    }, duration * .34);
    const step = now => {
      if (motion !== transition) return;
      const t = Math.min(1, (now - began) / duration);
      const eased = t < .5 ? 16 * t ** 5 : 1 - (-2 * t + 2) ** 5 / 2;
      scroller.scrollTop = start + (target - start) * eased;
      if (t < 1) transition.frame = requestAnimationFrame(step);
      else {
        scroller.style.scrollBehavior = transition.previousBehavior;
        motion = null;
        delete root.dataset.phaseTransition;
        heading.tabIndex = -1;
        heading.focus({ preventScroll: true });
        schedule();
      }
    };
    transition.frame = requestAnimationFrame(step);
    schedule();
  }

  document.addEventListener('click', event => {
    if (!(event.target instanceof Element)) return;
    if (event.target.closest('[data-flooder-reload]')) {
      event.preventDefault();
      event.stopImmediatePropagation();
      startLoading();
      requestAnimationFrame(() => requestAnimationFrame(() => location.reload()));
      return;
    }
    const link = event.target.closest('.phase-link');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    goToPhase(link);
  }, { signal: events.signal });

  document.addEventListener('keydown', event => {
    const menu = event.target instanceof Element ? event.target.closest('[data-testid="stMainMenuList"]') : null;
    if (!menu || !menu.querySelector('[data-flooder-reload]')) return;
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    const items = [...menu.querySelectorAll('[role^="menuitem"]:not(:disabled)')];
    const index = items.indexOf(document.activeElement);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1
      : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
    event.preventDefault();
    event.stopImmediatePropagation();
    items.forEach((item, i) => item.tabIndex = i === next ? 0 : -1);
    items[next]?.focus();
  }, { capture: true, signal: events.signal });

  document.addEventListener('wheel', cancelMotion, { passive: true, signal: events.signal });
  document.addEventListener('touchstart', cancelMotion, { passive: true, signal: events.signal });
  document.addEventListener('keydown', event => {
    if (['PageUp', 'PageDown', 'Home', 'End', 'ArrowUp', 'ArrowDown'].includes(event.key)) cancelMotion();
  }, { signal: events.signal });
  document.addEventListener('scroll', schedule, { passive: true, capture: true, signal: events.signal });
  window.addEventListener('resize', schedule, { passive: true, signal: events.signal });
  document.addEventListener('load', schedule, { capture: true, signal: events.signal });
  const observer = new MutationObserver(schedule);
  observer.observe(document.body, {
    subtree: true, childList: true, attributes: true,
    attributeFilter: ['class', 'style', 'data-test-script-state', 'data-test-connection-state', 'aria-expanded']
  });
  window.flooderInterface = {
    version, refresh: schedule,
    destroy() { events.abort(); observer.disconnect(); cancelMotion(); orbital?.destroy(); if (boot) finishLoading(); }
  };
  if (!window.flooderBootSeen) { window.flooderBootSeen = true; startLoading(); }
  schedule();
})();
