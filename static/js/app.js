const burger = document.getElementById('burger');
const nav = document.getElementById('nav');
const header = document.getElementById('header');

if (burger && nav) {
  const navLinks = nav.querySelectorAll('a');

  function toggleMenu(forceClose = false) {
    const isOpen = forceClose ? false : !nav.classList.contains('open');
    nav.classList.toggle('open', isOpen);
    burger.classList.toggle('active', isOpen);
    burger.setAttribute('aria-expanded', isOpen);
    document.body.classList.toggle('menu-open', isOpen);
  }

  burger.addEventListener('click', () => toggleMenu());
  navLinks.forEach((link) => link.addEventListener('click', () => toggleMenu(true)));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') toggleMenu(true);
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) toggleMenu(true);
  });
}

/* ==========================================================================
   Шапка
   ========================================================================== */

if (header) {
  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 10);
  });
}

/* ==========================================================================
    C.I.N.E.M.A
   ========================================================================== */

const logoBtn = document.getElementById('logo');
const cinemaPopup = document.getElementById('cinema-popup');

if (logoBtn && cinemaPopup) {
  logoBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    cinemaPopup.classList.toggle('show');
  });
  document.addEventListener('click', (e) => {
    if (!cinemaPopup.contains(e.target) && e.target !== logoBtn) {
      cinemaPopup.classList.remove('show');
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') cinemaPopup.classList.remove('show');
  });
}

/* ==========================================================================
   Картки фільмів
   ========================================================================== */

document.querySelectorAll('.poster-clickable').forEach((poster) => {
  poster.addEventListener('click', (e) => {
    e.stopPropagation();
    const popup = poster.querySelector('.movie-popup');
    document.querySelectorAll('.movie-popup.show').forEach((p) => {
      if (p !== popup) p.classList.remove('show');
    });
    popup.classList.toggle('show');
  });
});

document.addEventListener('click', () => {
  document.querySelectorAll('.movie-popup.show').forEach((p) => p.classList.remove('show'));
});

/* ==========================================================================
   Лічильники 
   ========================================================================== */

function animateCounter(el) {
  const target = Number(el.dataset.target) || 0;
  const duration = 1500;
  const start = performance.now();

  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(target * eased);
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

const counters = document.querySelectorAll('.counter');
if (counters.length) {
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });
  counters.forEach((c) => counterObserver.observe(c));
}

/* ==========================================================================
   Поява 
   ========================================================================== */

const revealTargets = document.querySelectorAll(
  '.section-title, .feature-card, .step, .promo, .cta, .stat, .movie-card, .gallery-card, .about-text, .contacts-list, .bookings-table, .footer-grid'
);

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      entry.target.style.transitionDelay = '';
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

revealTargets.forEach((el, i) => {
  el.classList.add('reveal');
  el.style.transitionDelay = (i % 4) * 0.08 + 's';
  revealObserver.observe(el);
});

/* ==========================================================================
   Перемикач 
   ========================================================================== */

const animToggle = document.getElementById('anim-toggle');
if (animToggle) {
  animToggle.checked = localStorage.getItem('noAnim') === '1';
  animToggle.addEventListener('change', () => {
    localStorage.setItem('noAnim', animToggle.checked ? '1' : '0');
    document.documentElement.classList.toggle('no-anim', animToggle.checked);
  });
}