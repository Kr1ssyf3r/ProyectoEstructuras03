document.addEventListener("DOMContentLoaded", () => {

    // =========================================
    // MODO CLARO Y OSCURO
    // Misma clave que usan login.js, inicio.js y amigos.js,
    // así el tema elegido en otra pantalla se mantiene aquí.
    // =========================================

    const THEME_KEY = "social-una-theme";
    const html = document.documentElement;
    const themeToggle = document.getElementById("themeToggle");

    // Aplicar el tema guardado
    html.setAttribute(
        "data-theme",
        localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark"
    );

    // Texto del botón para lectores de pantalla
    function actualizarAccesibilidad() {
        if (!themeToggle) {
            return;
        }

        const oscuro = html.getAttribute("data-theme") === "dark";

        themeToggle.setAttribute(
            "aria-label",
            oscuro ? "Activar modo claro" : "Activar modo oscuro"
        );

        themeToggle.title = oscuro
            ? "Cambiar a modo claro"
            : "Cambiar a modo oscuro";
    }

    // Cambiar el tema al hacer clic
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const oscuro = html.getAttribute("data-theme") === "dark";
            const nuevoTema = oscuro ? "light" : "dark";

            html.setAttribute("data-theme", nuevoTema);
            localStorage.setItem(THEME_KEY, nuevoTema);

            actualizarAccesibilidad();
        });
    }

    actualizarAccesibilidad();

});