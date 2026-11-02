
document.addEventListener("DOMContentLoaded", () => {

    const botonTema = document.getElementById("themeToggle");
    const documento = document.documentElement;

    // Recuperar el tema guardado.
    const temaGuardado = localStorage.getItem("socialuna-theme");

    if (temaGuardado) {
        documento.setAttribute("data-theme", temaGuardado);
    }

    // Actualizar el texto accesible del botón.
    function actualizarBotonTema() {
        if (!botonTema) return;

        const temaOscuro =
            documento.getAttribute("data-theme") === "dark";

        botonTema.setAttribute(
            "aria-label",
            temaOscuro
                ? "Activar modo claro"
                : "Activar modo oscuro"
        );
    }

    actualizarBotonTema();

    // Cambiar entre modo claro y oscuro.
    if (botonTema) {
        botonTema.addEventListener("click", () => {

            const temaActual =
                documento.getAttribute("data-theme");

            const nuevoTema =
                temaActual === "dark" ? "light" : "dark";

            documento.setAttribute("data-theme", nuevoTema);

            localStorage.setItem(
                "socialuna-theme",
                nuevoTema
            );

            actualizarBotonTema();
        });
    }

});
