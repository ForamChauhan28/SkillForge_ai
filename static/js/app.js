/* ═══════════════════════════════════════════════════
   SkillForge AI — Global JavaScript
   Theme toggle, common utilities, animations
   ═══════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initMobileMenu();
    initFlashDismiss();
    initAnimations();
});


/* ═══════════════ Global Particles ═══════════════ */

function initParticles() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    for (let i = 0; i < 50; i++) {
        const p = document.createElement('div');
        p.classList.add('particle');
        const size = Math.random() * 6 + 2;
        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${Math.random() * 100}%`;
        p.style.animationDuration = `${Math.random() * 15 + 10}s`;
        p.style.animationDelay = `-${Math.random() * 20}s`;
        particlesContainer.appendChild(p);
    }
}


/* ═══════════════ Mobile Menu ═══════════════ */

function initMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.getElementById('navLinks');
    if (!menuToggle || !navLinks) return;

    menuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('open');
        menuToggle.textContent = navLinks.classList.contains('open') ? '✕' : '☰';
    });

    // Close menu when clicking a link
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('open');
            menuToggle.textContent = '☰';
        });
    });
}


/* ═══════════════ Flash Messages ═══════════════ */

function initFlashDismiss() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);

        // Click to dismiss
        alert.style.cursor = 'pointer';
        alert.addEventListener('click', () => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        });
    });
}


/* ═══════════════ Scroll Animations ═══════════════ */

function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}


/* ═══════════════ Loading Overlay ═══════════════ */

function showLoading(text = 'Processing...', subtext = 'This may take a few seconds') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const loadingSub = document.getElementById('loadingSubtext');
    if (overlay) {
        loadingText.textContent = text;
        loadingSub.textContent = subtext;
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
}


/* ═══════════════ API Helper ═══════════════ */

async function apiCall(url, options = {}) {
    const defaults = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const config = { ...defaults, ...options };
    if (options.headers) {
        config.headers = { ...defaults.headers, ...options.headers };
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function apiPost(url, body) {
    return apiCall(url, {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

async function apiGet(url) {
    return apiCall(url, { method: 'GET' });
}


/* ═══════════════ Toast Notifications ═══════════════ */

function showToast(message, type = 'success', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 10000;
        min-width: 300px;
        max-width: 450px;
        box-shadow: var(--shadow-lg);
        animation: fadeInDown 0.4s ease-out;
    `;

    const icons = { success: '✅', danger: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `${icons[type] || ''} ${message}`;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}


/* ═══════════════ Utility Functions ═══════════════ */

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
