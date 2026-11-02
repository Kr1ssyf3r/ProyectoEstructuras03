document.addEventListener('DOMContentLoaded', () => {
    // Coincide con la clave que utiliza login.js.
    const THEME_KEY = 'social-una-theme';
    const html = document.documentElement;
    const themeToggle = document.getElementById('themeToggle');

    html.setAttribute('data-theme', localStorage.getItem(THEME_KEY) || 'light');

    function actualizarTemaAccesible() {
        if (!themeToggle) return;
        const oscuro = html.getAttribute('data-theme') === 'dark';
        themeToggle.setAttribute('aria-label', oscuro ? 'Activar modo claro' : 'Activar modo oscuro');
        themeToggle.title = oscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
    }
    actualizarTemaAccesible();

    themeToggle?.addEventListener('click', () => {
        const nuevo = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', nuevo);
        localStorage.setItem(THEME_KEY, nuevo);
        actualizarTemaAccesible();
    });

    const contenedor = document.querySelector('.friends-container');
    if (!contenedor) return;
    const pestanas = [...document.querySelectorAll('.friends-tab')];
    const paneles = [...document.querySelectorAll('.friends-panel')];
    const nombresValidos = pestanas.map(p => p.dataset.tab);

    function mostrarPestana(nombre) {
        if (!nombresValidos.includes(nombre)) return;
        pestanas.forEach(p => p.setAttribute('aria-selected', String(p.dataset.tab === nombre)));
        paneles.forEach(p => { p.hidden = p.id !== `panel-${nombre}`; });
        history.replaceState(null, '', `#${nombre}`);
    }

    pestanas.forEach(p => p.addEventListener('click', () => mostrarPestana(p.dataset.tab)));
    document.querySelectorAll('[data-ir-a]').forEach(b =>
        b.addEventListener('click', () => mostrarPestana(b.dataset.irA)));

    const hash = window.location.hash.slice(1);
    const inicial = nombresValidos.includes(hash) ? hash : contenedor.dataset.tabInicial || 'amigos';
    mostrarPestana(inicial);

    document.querySelectorAll('form[data-confirmar]').forEach(form => {
        form.addEventListener('submit', evento => {
            if (!window.confirm(form.dataset.confirmar)) evento.preventDefault();
        });
    });
});
