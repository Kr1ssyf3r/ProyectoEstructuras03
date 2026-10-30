
// =========================================
// MOSTRAR Y OCULTAR CONTRASEÑAS
// =========================================

function configurarVisibilidadContrasena(inputId, botonId) {

    const passwordInput = document.getElementById(inputId);
    const passwordToggle = document.getElementById(botonId);

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
}


// Configurar ambos campos de contraseña.
configurarVisibilidadContrasena(
    "contrasena",
    "password-toggle"
);

configurarVisibilidadContrasena(
    "confirmar_contrasena",
    "confirm-password-toggle"
);


// =========================================
// VALIDAR QUE LAS CONTRASEÑAS COINCIDAN
// =========================================

const formulario = document.querySelector("form");

const contrasena = document.getElementById("contrasena");
const confirmarContrasena = document.getElementById(
    "confirmar_contrasena"
);


function validarContrasenas() {

    if (confirmarContrasena.value === "") {
        confirmarContrasena.setCustomValidity("");
        return;
    }

    if (contrasena.value !== confirmarContrasena.value) {
        confirmarContrasena.setCustomValidity(
            "Las contraseñas no coinciden."
        );
    } else {
        confirmarContrasena.setCustomValidity("");
    }

}


contrasena.addEventListener("input", validarContrasenas);
confirmarContrasena.addEventListener("input", validarContrasenas);

formulario.addEventListener("submit", (evento) => {

    validarContrasenas();

    if (!formulario.checkValidity()) {
        evento.preventDefault();
        formulario.reportValidity();
    }

});


// =========================================
// CAMBIAR ENTRE MODO CLARO Y OSCURO
// =========================================

const themeToggle = document.getElementById("theme-toggle");
const html = document.documentElement;


// Recuperar el tema guardado.
const temaGuardado = localStorage.getItem("social-una-theme");

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
