(() => {
    //busca el input de "Buscar personas" dentro del formulario de busqueda
    const input = document.querySelector('.friends-search input[name="q"]');
    if (!input) return;

    //se crea la caja de sugerencias y se pega dentro del contenedor del input
    const caja = document.createElement("ul");
    caja.className = "autocompletar";
    caja.hidden = true;
    input.closest(".input-container").appendChild(caja);

    let temporizador;
    let controlador;

    const pintar = (items) => {
        caja.replaceChildren();

        items.forEach((u) => {
            const li = document.createElement("li");

            const nombre = document.createElement("strong");
            nombre.textContent = u.nombre;      //textContent evita que un nombre con HTML se ejecute (XSS)

            const alias = document.createElement("span");
            alias.textContent = "@" + u.usuario;

            li.append(nombre, alias);

            //mousedown y no click, porque el blur del input oculta la caja antes de que el click termine
            li.addEventListener("mousedown", () => {
                input.value = u.usuario;
                input.form.submit();
            });

            caja.appendChild(li);
        });

        caja.hidden = items.length === 0;
    };

    input.addEventListener("input", () => {
        clearTimeout(temporizador);

        const q = input.value.trim();
        if (!q) {
            caja.hidden = true;
            return;
        }

        //debounce: espera 150 ms despues de la ultima tecla para no hacer una peticion por letra
        temporizador = setTimeout(async () => {
            //si habia una peticion en vuelo, se cancela para que una respuesta vieja no pise a la nueva
            controlador?.abort();
            controlador = new AbortController();

            try {
                const r = await fetch(
                    "/amigos/autocompletar?q=" + encodeURIComponent(q),
                    { signal: controlador.signal }
                );
                if (r.ok) pintar(await r.json());
            } catch (e) {
                //peticion cancelada, no hay nada que hacer
            }
        }, 150);
    });

    input.addEventListener("blur", () => { caja.hidden = true; });
})();