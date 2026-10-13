// NutriTrack Main JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // Mobile Drawer Toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const closeDrawerBtn = document.getElementById('closeMobileDrawer');
    const drawer = document.getElementById('mobileDrawer');

    if (mobileBtn && drawer) {
        mobileBtn.addEventListener('click', () => {
            drawer.classList.remove('hidden');
        });
    }

    if (closeDrawerBtn && drawer) {
        closeDrawerBtn.addEventListener('click', () => {
            drawer.classList.add('hidden');
        });
    }

    // Auto-dismiss Flash Messages after 6 seconds
    const flashes = document.querySelectorAll('.flash-alert');
    flashes.forEach(flash => {
        setTimeout(() => {
            if (flash && flash.parentElement) {
                flash.style.opacity = '0';
                flash.style.transform = 'translateY(-10px)';
                setTimeout(() => flash.remove(), 300);
            }
        }, 5000);
    });

    // Close Modals on Escape Key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('[id$="Modal"]').forEach(modal => {
                modal.classList.add('hidden');
            });
            if (drawer) drawer.classList.add('hidden');
        }
    });
});

/**
 * Global Toast Notification Helper
 * @param {string} message
 * @param {'success'|'danger'|'info'|'warning'} type
 */
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item flex items-center justify-between p-3.5 rounded-xl shadow-lg border text-xs font-semibold max-w-sm ${
        type === 'success' ? 'bg-emerald-900 text-white border-emerald-700' :
        type === 'danger' ? 'bg-rose-900 text-white border-rose-700' :
        type === 'warning' ? 'bg-amber-900 text-white border-amber-700' :
        'bg-slate-900 text-white border-slate-700'
    }`;

    const iconClass = type === 'success' ? 'fa-circle-check text-emerald-400' :
                      type === 'danger' ? 'fa-circle-exclamation text-rose-400' :
                      type === 'warning' ? 'fa-triangle-exclamation text-amber-400' :
                      'fa-circle-info text-sky-400';

    toast.innerHTML = `
        <div class="flex items-center gap-2.5">
            <i class="fa-solid ${iconClass} text-sm"></i>
            <span>${message}</span>
        </div>
        <button class="text-slate-400 hover:text-white ml-3" onclick="dismissToast(this.parentElement)">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        dismissToast(toast);
    }, 4000);
}

function dismissToast(toastEl) {
    if (!toastEl) return;
    toastEl.classList.add('dismissing');
    setTimeout(() => {
        toastEl.remove();
    }, 250);
}
