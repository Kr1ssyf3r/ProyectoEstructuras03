(() => {
    const $ = (id) => document.getElementById(id);

    const modalCamara = $("modalCamara");
    if (!modalCamara) return;

    const preview = $("previewCamara");
    const foto = $("fotoCapturada");
    const videoGrabado = $("videoGrabado");
    const error = $("errorCamara");
    const btnFoto = $("btnFoto");
    const btnGrabar = $("btnGrabar");
    const btnRepetir = $("btnRepetir");
    const btnSubir = $("btnSubir");

    const DURACION_MAX_MS = 15000;   //limite de grabacion
    const DURACION_FOTO_MS = 5000;   //cuanto dura una foto en el visor

    let stream = null;
    let recorder = null;
    let blobFinal = null;
    let extension = "png";
    let temporizadorGrabacion = null;

    //---------- utilidades ----------
    const mostrarError = (texto) => {
        error.textContent = texto;
        error.hidden = !texto;
    };

    const detenerCamara = () => {
        stream?.getTracks().forEach((t) => t.stop());   //apaga la luz de la camara
        stream = null;
    };

    //cada formato por navegador: Chrome/Firefox webm, Safari mp4
    const formatoVideo = () => {
        for (const tipo of ["video/webm", "video/mp4"]) {
            if (MediaRecorder.isTypeSupported(tipo)) return tipo;
        }
        return "";
    };

    const reiniciarVista = () => {
        blobFinal = null;
        foto.hidden = true;
        videoGrabado.hidden = true;
        videoGrabado.removeAttribute("src");
        preview.hidden = false;
        btnFoto.hidden = false;
        btnGrabar.hidden = false;
        btnRepetir.hidden = true;
        btnSubir.hidden = true;
        btnGrabar.textContent = "Grabar";
    };

    const mostrarResultado = () => {
        preview.hidden = true;
        btnFoto.hidden = true;
        btnGrabar.hidden = true;
        btnRepetir.hidden = false;
        btnSubir.hidden = false;
    };

    //---------- abrir y cerrar la camara ----------
    $("abrirCamara").addEventListener("click", async () => {
        mostrarError("");
        reiniciarVista();
        modalCamara.hidden = false;

        //getUserMedia solo existe en localhost o HTTPS
        if (!navigator.mediaDevices?.getUserMedia) {
            mostrarError("Este navegador o esta direccion no permite usar la camara (usa localhost o HTTPS).");
            return;
        }

        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            preview.srcObject = stream;
        } catch (e) {
            mostrarError(
                e.name === "NotAllowedError" ? "Permiso de camara denegado."
                : e.name === "NotFoundError" ? "No se encontro ninguna camara."
                : "No se pudo abrir la camara (puede estar en uso)."
            );
        }
    });

    $("btnCerrarCamara").addEventListener("click", () => {
        clearTimeout(temporizadorGrabacion);
        if (recorder?.state === "recording") recorder.stop();
        detenerCamara();
        modalCamara.hidden = true;
    });

    //---------- foto ----------
    btnFoto.addEventListener("click", () => {
        if (!stream) return;

        //se dibuja el frame actual del video en un canvas y se exporta como PNG
        const canvas = document.createElement("canvas");
        canvas.width = preview.videoWidth;
        canvas.height = preview.videoHeight;
        canvas.getContext("2d").drawImage(preview, 0, 0);

        canvas.toBlob((blob) => {
            blobFinal = blob;
            extension = "png";
            foto.src = URL.createObjectURL(blob);
            foto.hidden = false;
            mostrarResultado();
        }, "image/png");
    });

    //---------- video ----------
    btnGrabar.addEventListener("click", () => {
        if (!stream) return;

        //segundo clic: detiene la grabacion
        if (recorder?.state === "recording") {
            recorder.stop();
            return;
        }

        const tipo = formatoVideo();
        if (!tipo) {
            mostrarError("Este navegador no puede grabar video.");
            return;
        }

        const trozos = [];
        recorder = new MediaRecorder(stream, { mimeType: tipo });
        recorder.ondataavailable = (e) => e.data.size && trozos.push(e.data);

        recorder.onstop = () => {
            clearTimeout(temporizadorGrabacion);
            blobFinal = new Blob(trozos, { type: tipo });
            extension = tipo.includes("mp4") ? "mp4" : "webm";
            videoGrabado.src = URL.createObjectURL(blobFinal);
            videoGrabado.hidden = false;
            mostrarResultado();
        };

        recorder.start();
        btnGrabar.textContent = "Detener";
        temporizadorGrabacion = setTimeout(() => recorder.stop(), DURACION_MAX_MS);
    });

    btnRepetir.addEventListener("click", reiniciarVista);

    //---------- subir ----------
    btnSubir.addEventListener("click", async () => {
        if (!blobFinal) return;
        btnSubir.disabled = true;

        const datos = new FormData();
        //el tercer parametro es el nombre provisional: solo sirve para que el servidor lea la extension
        datos.append("archivo", blobFinal, `historia.${extension}`);
        datos.append("csrf_token", $("csrfHistorias").value);

        try {
            const r = await fetch("/historias/crear", { method: "POST", body: datos });
            if (r.ok || r.redirected) {
                detenerCamara();
                location.reload();   //recarga para ver la barra actualizada
            } else {
                mostrarError("No se pudo publicar la historia.");
            }
        } catch (e) {
            mostrarError("Error de red al subir la historia.");
        } finally {
            btnSubir.disabled = false;
        }
    });

    //---------- visor ----------
    const grupos = JSON.parse($("datosHistorias")?.textContent || "[]");
    const modalVisor = $("modalVisor");
    const contenido = $("contenidoVisor");
    const progreso = $("progresoVisor");

    let temporizadorVisor = null;
    let grupoActual = 0;
    let indiceActual = 0;

    const cerrarVisor = () => {
        clearTimeout(temporizadorVisor);
        contenido.replaceChildren();
        modalVisor.hidden = true;
    };

    const siguiente = () => {
        const grupo = grupos[grupoActual];
        if (indiceActual < grupo.historias.length - 1) {
            indiceActual++;
            mostrarHistoria();
        } else if (grupoActual < grupos.length - 1) {
            grupoActual++;
            indiceActual = 0;
            mostrarHistoria();
        } else {
            cerrarVisor();
        }
    };

    function mostrarHistoria() {
        clearTimeout(temporizadorVisor);
        const grupo = grupos[grupoActual];
        const h = grupo.historias[indiceActual];

        $("autorVisor").textContent = grupo.autor;

        //una barrita por historia del autor: llenas las vistas, vacias las pendientes
        progreso.replaceChildren(
            ...grupo.historias.map((_, i) => {
                const barra = document.createElement("span");
                barra.className = i <= indiceActual ? "llena" : "";
                return barra;
            })
        );

        contenido.replaceChildren();

        if (h.tipo === "imagen") {
            const img = document.createElement("img");
            img.src = h.url;
            contenido.appendChild(img);
            temporizadorVisor = setTimeout(siguiente, DURACION_FOTO_MS);
        } else {
            const v = document.createElement("video");
            v.src = h.url;
            v.autoplay = true;
            v.playsInline = true;
            v.onended = siguiente;   //pasa a la siguiente al terminar el video
            contenido.appendChild(v);
        }
    }

    document.querySelectorAll("[data-grupo]").forEach((boton) => {
        boton.addEventListener("click", () => {
            grupoActual = Number(boton.dataset.grupo);
            indiceActual = 0;
            modalVisor.hidden = false;
            mostrarHistoria();
        });
    });

    //clic en la mitad izquierda retrocede, en la derecha avanza
    contenido.addEventListener("click", (e) => {
        const mitad = contenido.getBoundingClientRect().left + contenido.clientWidth / 2;
        if (e.clientX < mitad && indiceActual > 0) {
            indiceActual--;
            mostrarHistoria();
        } else {
            siguiente();
        }
    });

    $("btnCerrarVisor").addEventListener("click", cerrarVisor);
})();