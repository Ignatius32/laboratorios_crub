/**
 * Comportamiento de interfaz compartido.
 *
 * Tres cosas que faltaban en toda la aplicación:
 *
 *   1. Estados de carga. Importar un Excel o sincronizar Keycloak tarda
 *      segundos y no daba ninguna señal: la gente volvía a apretar el botón y
 *      mandaba la operación dos veces.
 *   2. Mensajes flash que no empujen el contenido y se vayan solos.
 *   3. Confirmaciones delegadas, para que también funcionen en las filas que
 *      DataTables agrega al paginar (el manejador anterior consultaba el DOM
 *      una sola vez, al cargar, así que esas filas quedaban sin confirmación).
 */

(function () {
    'use strict';

    /* ----------------------------------------------------------------------
       Estado de carga en los envíos
       ---------------------------------------------------------------------- */

    /**
     * Pone un botón en estado "trabajando": spinner, texto en gerundio y
     * deshabilitado. Se deshabilita DESPUÉS de dejar que el submit salga, o el
     * navegador descarta el envío.
     */
    function marcarCargando(boton) {
        if (!boton || boton.dataset.cargando === 'true') {
            return;
        }
        boton.dataset.cargando = 'true';

        const textoNodo = boton.querySelector('.btn-texto');
        const textoCargando = boton.dataset.textoCargando;

        if (textoNodo && textoCargando) {
            boton.dataset.textoOriginal = textoNodo.textContent;
            textoNodo.textContent = textoCargando;
        }

        const spinner = document.createElement('span');
        spinner.className = 'btn-spinner';
        spinner.setAttribute('aria-hidden', 'true');
        boton.prepend(spinner);

        // aria-busy para que un lector de pantalla anuncie que está en curso.
        boton.setAttribute('aria-busy', 'true');

        // El disabled va en el siguiente ciclo: si se aplica ahora, Firefox y
        // Safari no envían el formulario.
        setTimeout(() => { boton.disabled = true; }, 0);
    }

    document.addEventListener('submit', function (evento) {
        const formulario = evento.target;
        if (formulario.dataset.sinCarga === 'true') {
            return;
        }
        // Un formulario inválido no llega a enviarse: dejar el botón como está.
        if (typeof formulario.checkValidity === 'function' && !formulario.checkValidity()) {
            return;
        }
        const boton = formulario.querySelector('button[type="submit"], input[type="submit"]');
        if (boton && boton.dataset.textoCargando !== undefined) {
            marcarCargando(boton);
        }
    }, true);

    /* ----------------------------------------------------------------------
       Mensajes flash
       ---------------------------------------------------------------------- */

    /**
     * Los descarta solos después de un rato. Los errores se quedan: quien
     * necesita leer un mensaje de error suele necesitar tiempo, y a veces
     * copiarlo.
     */
    function programarCierre(alerta) {
        const esError = alerta.classList.contains('alert-danger')
            || alerta.classList.contains('alert-error');
        if (esError) {
            return;
        }

        let temporizador = setTimeout(cerrar, 5000);

        // Si la persona está leyendo el mensaje, no cerrarlo debajo del cursor.
        alerta.addEventListener('mouseenter', () => clearTimeout(temporizador));
        alerta.addEventListener('mouseleave', () => { temporizador = setTimeout(cerrar, 2000); });

        function cerrar() {
            alerta.classList.add('saliendo');
            alerta.addEventListener('animationend', () => alerta.remove(), { once: true });
            // Si las animaciones están desactivadas el evento no llega nunca.
            setTimeout(() => alerta.remove(), 400);
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.flash-contenedor .alert').forEach(programarCierre);
    });

    const ICONOS = {
        success: 'fa-circle-check',
        danger: 'fa-circle-exclamation',
        warning: 'fa-triangle-exclamation',
        info: 'fa-circle-info'
    };

    /**
     * Muestra un aviso desde JavaScript, con el mismo aspecto que los mensajes
     * del servidor.
     *
     * Reemplaza a SweetAlert2, que se cargaba entero desde un CDN sólo para
     * tres mensajes, y al alert() del navegador que quedaba de respaldo.
     *
     * @param {string} mensaje
     * @param {'success'|'danger'|'warning'|'info'} [tipo]
     */
    window.mostrarAviso = function (mensaje, tipo) {
        tipo = tipo || 'info';

        let contenedor = document.querySelector('.flash-contenedor');
        if (!contenedor) {
            contenedor = document.createElement('div');
            contenedor.className = 'flash-contenedor';
            contenedor.setAttribute('role', 'status');
            contenedor.setAttribute('aria-live', 'polite');
            document.body.appendChild(contenedor);
        }

        const alerta = document.createElement('div');
        alerta.className = 'alert alert-' + tipo + ' alert-dismissible';
        alerta.setAttribute('role', 'alert');

        const icono = document.createElement('i');
        icono.className = 'fas ' + (ICONOS[tipo] || ICONOS.info) + ' mt-1';
        icono.setAttribute('aria-hidden', 'true');

        // textContent y no innerHTML: el mensaje puede venir del servidor y no
        // tiene por qué interpretarse como marcado.
        const texto = document.createElement('div');
        texto.textContent = mensaje;

        const cerrar = document.createElement('button');
        cerrar.type = 'button';
        cerrar.className = 'btn-close';
        cerrar.setAttribute('data-bs-dismiss', 'alert');
        cerrar.setAttribute('aria-label', 'Cerrar');

        alerta.append(icono, texto, cerrar);
        contenedor.appendChild(alerta);
        programarCierre(alerta);
    };

    /* ----------------------------------------------------------------------
       Confirmación de acciones destructivas
       ---------------------------------------------------------------------- */

    let modalConfirmacion = null;
    let accionPendiente = null;

    function construirModal() {
        if (document.getElementById('modalConfirmacion')) {
            return;
        }
        const marcado = `
        <div class="modal fade" id="modalConfirmacion" tabindex="-1"
             aria-labelledby="modalConfirmacionTitulo" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 class="modal-title h5" id="modalConfirmacionTitulo">Confirmar acción</h2>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"
                                aria-label="Cerrar"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-2" data-confirmacion-mensaje></p>
                        <p class="text-muted mb-0" style="font-size: var(--texto-sm)"
                           data-confirmacion-aviso></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-danger" data-confirmacion-aceptar>
                            Confirmar
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', marcado);

        const nodo = document.getElementById('modalConfirmacion');
        modalConfirmacion = new bootstrap.Modal(nodo);

        nodo.querySelector('[data-confirmacion-aceptar]').addEventListener('click', function () {
            modalConfirmacion.hide();
            const accion = accionPendiente;
            accionPendiente = null;
            if (accion) {
                // Después de que el modal termine de cerrarse, para que el
                // backdrop no quede colgado si la acción navega.
                nodo.addEventListener('hidden.bs.modal', accion, { once: true });
            }
        });
    }

    // Delegado en document: funciona con lo que exista ahora y con lo que se
    // agregue después.
    document.addEventListener('click', function (evento) {
        const disparador = evento.target.closest('.confirm-action');
        if (!disparador) {
            return;
        }

        evento.preventDefault();
        evento.stopPropagation();
        construirModal();

        const nodo = document.getElementById('modalConfirmacion');
        nodo.querySelector('[data-confirmacion-mensaje]').textContent =
            disparador.dataset.message || '¿Confirmás esta acción?';
        nodo.querySelector('[data-confirmacion-aviso]').textContent =
            disparador.dataset.warning || 'Esta acción no se puede deshacer.';

        const aceptar = nodo.querySelector('[data-confirmacion-aceptar]');
        aceptar.textContent = disparador.dataset.btnText || 'Confirmar';
        aceptar.className = 'btn ' + (disparador.dataset.btnClass || 'btn-danger');

        accionPendiente = function () {
            if (disparador.tagName === 'A') {
                window.location.href = disparador.getAttribute('href');
            } else if (disparador.form) {
                // requestSubmit y no submit(): dispara el evento y así el botón
                // toma su estado de carga y corre la validación del navegador.
                if (disparador.form.requestSubmit) {
                    disparador.form.requestSubmit(disparador);
                } else {
                    disparador.form.submit();
                }
            } else if (disparador.dataset.url) {
                window.location.href = disparador.dataset.url;
            }
        };

        modalConfirmacion.show();
    });

    /* ----------------------------------------------------------------------
       Detalles
       ---------------------------------------------------------------------- */

    document.addEventListener('DOMContentLoaded', function () {
        // Tooltips de Bootstrap 5. El código viejo usaba $(...).tooltip(), la
        // API jQuery de Bootstrap 4, que en la 5 lanza TypeError y cortaba el
        // resto del script.
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (nodo) {
            new bootstrap.Tooltip(nodo);
        });

        // Los filtros de listado se envían solos al cambiar un select: obliga
        // menos a buscar el botón "Aplicar".
        document.querySelectorAll('[data-filtro-auto] select').forEach(function (select) {
            select.addEventListener('change', function () {
                select.closest('form').requestSubmit();
            });
        });
    });
})();
