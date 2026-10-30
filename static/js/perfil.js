
document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById("themeToggle");
    const html = document.documentElement;

    // Recuperar el tema guardado o utilizar el tema claro.
    const temaGuardado = localStorage.getItem("socialuna-theme") || "light";
    html.setAttribute("data-theme", temaGuardado);

    // Cambiar el tema al presionar el botón.
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const temaActual = html.getAttribute("data-theme");
            const nuevoTema = temaActual === "dark" ? "light" : "dark";

            html.setAttribute("data-theme", nuevoTema);
            localStorage.setItem("socialuna-theme", nuevoTema);
        });
    }
});
