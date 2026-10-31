
// =========================================
// MOSTRAR Y OCULTAR CONTRASEÑA
// =========================================

const passwordInput = document.getElementById("contrasena");
const passwordToggle = document.getElementById("password-toggle");

passwordToggle.addEventListener("click", () => {

    const mostrar = passwordInput.type === "password";

    passwordInput.type = mostrar ? "text" : "password";

    passwordToggle.classList.toggle("is-visible", mostrar);

    passwordToggle.setAttribute(
        "aria-label",
        mostrar ? "Ocultar contraseña" : "Mostrar contraseña"
    );

    passwordToggle.setAttribute(
        "aria-pressed",
        String(mostrar)
    );

    passwordToggle.title = mostrar
        ? "Ocultar contraseña"
        : "Mostrar contraseña";

});


// =========================================
// CAMBIAR ENTRE MODO CLARO Y OSCURO
// =========================================

const themeToggle = document.getElementById("theme-toggle");
const html = document.documentElement;


// Recuperar el tema guardado.
const temaGuardado = localStorage.getItem("social-una-theme");


// Aplicar el tema guardado o utilizar el tema claro.
html.setAttribute(
    "data-theme",
    temaGuardado || "light"
);


// Actualizar el texto accesible del botón.
function actualizarBotonTema() {

    const modoOscuro = html.getAttribute("data-theme") === "dark";

    themeToggle.setAttribute(
        "aria-label",
        modoOscuro
            ? "Activar modo claro"
            : "Activar modo oscuro"
    );

    themeToggle.title = modoOscuro
        ? "Cambiar a modo claro"
        : "Cambiar a modo oscuro";

}


// Cambiar el tema al presionar el botón.
themeToggle.addEventListener("click", () => {

    const temaActual = html.getAttribute("data-theme");

    const nuevoTema = temaActual === "light"
        ? "dark"
        : "light";

    html.setAttribute("data-theme", nuevoTema);

    localStorage.setItem("social-una-theme", nuevoTema);

    actualizarBotonTema();

});


// Configuración inicial.
actualizarBotonTema();
