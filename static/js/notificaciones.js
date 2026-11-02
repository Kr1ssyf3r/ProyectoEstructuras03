
document.addEventListener("DOMContentLoaded", () => {

    // =========================================
    // NOTIFICACIONES DE AMISTAD - SOCIAL UNA
    // =========================================

    const URL_NOTIFICACIONES = "/api/amistades/notificaciones";

    // Consultar cada 15 segundos.
    const INTERVALO = 15000;

    // Elementos que muestran la cantidad de solicitudes.
    const contadores = document.querySelectorAll(
        "[data-notification-count]"
    );

    // Indicadores visuales de notificaciones.
    const avisos = document.querySelectorAll(
        "[data-notification-alert]"
    );


    // =========================================
    // ACTUALIZAR CONTADORES
    // =========================================

    function actualizarContadores(cantidad) {

        contadores.forEach(contador => {

            contador.textContent = cantidad > 99
                ? "99+"
                : String(cantidad);

            contador.hidden = cantidad === 0;

        });

    }


    // =========================================
    // MOSTRAR U OCULTAR AVISOS
    // =========================================

    function actualizarAvisos(cantidad) {

        avisos.forEach(aviso => {

            aviso.hidden = cantidad === 0;

            const texto = aviso.querySelector(
                "[data-notification-message]"
            );

            if (texto) {

                texto.textContent = cantidad === 1
                    ? "Tenés 1 solicitud de amistad pendiente."
                    : `Tenés ${cantidad} solicitudes de amistad pendientes.`;

            }

        });

    }


    // =========================================
    // CONSULTAR EL SERVIDOR FLASK
    // =========================================

    async function consultarNotificaciones() {

        // No consultar si la pestaña está oculta.
        if (document.hidden) {
            return;
        }

        try {

            const respuesta = await fetch(URL_NOTIFICACIONES, {
                method: "GET",
                credentials: "same-origin",
                cache: "no-store"
            });

            // Si la sesión expiró, Flask puede
            // redirigir al inicio de sesión.
            if (!respuesta.ok || respuesta.redirected) {
                    return;
                }

            const tipoContenido = respuesta.headers.get("content-type") || "";

            if (!tipoContenido.includes("application/json")) {
                return;
            }

            const datos = await respuesta.json();

            if (
                typeof datos.cantidad !== "number" ||
                !Number.isInteger(datos.cantidad) ||
                datos.cantidad < 0
            ) {
                return;
            }

            actualizarContadores(datos.cantidad);
            actualizarAvisos(datos.cantidad);

        } catch (error) {

            // Un fallo de conexión no debe bloquear
            // las demás funciones de Social UNA.
            console.error(
                "No se pudieron consultar las notificaciones:",
                error
            );

        }

    }


    // =========================================
    // CONSULTA INICIAL Y ACTUALIZACIONES
    // =========================================

    consultarNotificaciones();

    const intervaloNotificaciones = setInterval(
        consultarNotificaciones,
        INTERVALO
    );

    // Consultar inmediatamente al regresar
    // a la pestaña del navegador.
    document.addEventListener("visibilitychange", () => {

        if (!document.hidden) {
            consultarNotificaciones();
        }

    });

    // Detener consultas cuando se abandona la página.
    window.addEventListener("pagehide", () => {
        clearInterval(intervaloNotificaciones);
    });

});
