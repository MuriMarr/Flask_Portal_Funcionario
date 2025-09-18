(function () {
  // Reveal on scroll
  const reveals = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) e.target.classList.add('visible');
    });
  }, { threshold: 0.15 });

  reveals.forEach(r => observer.observe(r));

  // Optional: gentler mouse-based tilt for .tilt elements
  const tiltEls = document.querySelectorAll('.tilt');
  tiltEls.forEach(el => {
    el.addEventListener('mousemove', (ev) => {
      const rect = el.getBoundingClientRect();
      const x = ev.clientX - rect.left;
      const y = ev.clientY - rect.top;
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      const dx = (x - cx) / cx;
      const dy = (y - cy) / cy;
      const rx = (dy * 4).toFixed(2);
      const ry = (dx * -4).toFixed(2);
      el.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg) translateZ(6px)`;
    });
    el.addEventListener('mouseleave', () => {
      el.style.transform = '';
    });
  });
})();