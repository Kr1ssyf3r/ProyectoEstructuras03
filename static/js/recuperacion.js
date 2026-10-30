
document.addEventListener("DOMContentLoaded", () => {

    const botonTema = document.getElementById("theme-toggle");
    const html = document.documentElement;
    const metaTheme = document.querySelector('meta[name="theme-color"]');

    // Recuperar el tema guardado o utilizar el tema claro.
    const temaGuardado = localStorage.getItem("socialuna-theme");
    const temaInicial = temaGuardado || "light";

    aplicarTema(temaInicial);

    // Cambiar el tema al pulsar el botón.
    if (botonTema) {
        botonTema.addEventListener("click", () => {

            const temaActual = html.getAttribute("data-theme");

            const nuevoTema = temaActual === "dark"
                ? "light"
                : "dark";

            aplicarTema(nuevoTema);

            // Guardar la preferencia del usuario.
            localStorage.setItem("socialuna-theme", nuevoTema);
        });
    }

    /**
     * Aplica el tema visual de la página.
     */
    function aplicarTema(tema) {

        html.setAttribute("data-theme", tema);

        // Actualizar el color de la barra del navegador.
        if (metaTheme) {
            metaTheme.setAttribute(
                "content",
                tema === "dark" ? "#151e30" : "#f1f5fc"
            );
        }

        // Actualizar la descripción accesible del botón.
        if (botonTema) {
            const modoOscuroActivo = tema === "dark";

            botonTema.setAttribute(
                "aria-label",
                modoOscuroActivo
                    ? "Activar modo claro"
                    : "Activar modo oscuro"
            );
        }
    }

});
