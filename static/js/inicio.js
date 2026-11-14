
document.addEventListener("DOMContentLoaded", () => {

    // =========================================
    // MODO CLARO Y OSCURO
    // =========================================

    const html = document.documentElement;
    const themeToggle = document.getElementById("themeToggle");

    // Misma clave utilizada por login.js
    const THEME_KEY = "social-una-theme";

    // Recuperar tema guardado
    const temaGuardado = localStorage.getItem(THEME_KEY);

    html.setAttribute(
        "data-theme",
        temaGuardado === "light" ? "light" : "dark"
    );


    // =========================================
    // ACTUALIZAR ACCESIBILIDAD
    // =========================================

    function actualizarAccesibilidad() {

        if (!themeToggle) {
            return;
        }

        const oscuro =
            html.getAttribute("data-theme") === "dark";

        themeToggle.setAttribute(
            "aria-label",
            oscuro ? "Activar modo claro" : "Activar modo oscuro"
        );

        themeToggle.title = oscuro
            ? "Cambiar a modo claro"
            : "Cambiar a modo oscuro";
    }


    // =========================================
    // EVENTO DE CAMBIO DE TEMA
    // =========================================

    if (themeToggle) {

        themeToggle.addEventListener("click", () => {

            const oscuro =
                html.getAttribute("data-theme") === "dark";

            const nuevoTema = oscuro ? "light" : "dark";

            html.setAttribute("data-theme", nuevoTema);

            localStorage.setItem(THEME_KEY, nuevoTema);

            actualizarAccesibilidad();
        });

    }

    actualizarAccesibilidad();

});
