/* Attach the server token only to same-origin mutations. */
(() => {
    const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const originalFetch = window.fetch.bind(window);
    window.fetch = (input, options = {}) => {
        const url = new URL(input instanceof Request ? input.url : input, location.href);
        const method = String(options.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
        if (url.origin === location.origin && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
            const headers = new Headers(options.headers || (input instanceof Request ? input.headers : undefined));
            headers.set('X-CSRF-Token', token);
            options = { ...options, headers };
        }
        return originalFetch(input, options);
    };
    document.addEventListener('htmx:configRequest', event => {
        const url = new URL(event.detail.path, location.href);
        if (url.origin === location.origin) event.detail.headers['X-CSRF-Token'] = token;
    });
    // Includes forms constructed by existing JS modules after page load.
    const protectForm = form => {
        if (!form.matches('form') || String(form.method).toUpperCase() !== 'POST') return;
        if (new URL(form.action, location.href).origin !== location.origin) return;
        if (!form.querySelector('input[name="csrf_token"]')) {
            const field = document.createElement('input');
            field.type = 'hidden'; field.name = 'csrf_token'; field.value = token;
            form.appendChild(field);
        }
    };
    document.addEventListener('submit', event => protectForm(event.target), true);
    document.addEventListener('DOMContentLoaded', () => document.querySelectorAll('form').forEach(protectForm));
})();
