document.addEventListener("DOMContentLoaded", () => {

    const hiddenArgomento = document.getElementById('selectedArgomento');
    const modalitaHidden = document.getElementById('modalitaHidden');
    const form = document.getElementById('formScenario');

    const container = document.getElementById('carouselContainer');

    // EVENT DELEGATION: cattura il click anche se l'elemento è annidato
    container.addEventListener('click', (e) => {
        const card = e.target.closest('.carousel-item');
        if (!card) return;

        // rimuove selezione
        container.querySelectorAll('.carousel-item').forEach(c => c.classList.remove('selected'));

        // seleziona card cliccata
        card.classList.add('selected');

        // prende argomento da data-argomento
        const argomento = card.dataset.argomento;

        // SALVA NEL CAMPO NASCOSTO
        hiddenArgomento.value = argomento;

        console.log("Argomento selezionato:", argomento);
    });

    // Toastr
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-bottom-center",
        timeOut: 5000,
        extendedTimeOut: 1000,
        showMethod: "fadeIn",
        hideMethod: "fadeOut",
    };

    // errori URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('error')) {
        const errorType = urlParams.get('error');
        switch (errorType) {
            case 'DatiObbligatori':
                toastr.error("Tutti i campi sono obbligatori. Riprova.");
                break;
            case 'formatoTitolo':
                toastr.error("Il formato del titolo è errato. Riprova.");
                break;
            case 'formatoDescrizione':
                toastr.error("Il formato della descrizione è errato. Riprova.");
                break;
            case 'argomentoNonValido':
                toastr.error("L'argomento selezionato non è valido. Riprova.");
                break;
            default:
                toastr.error("Si è verificato un errore sconosciuto. Riprova.");
                break;
        }
        const cleanUrl = window.location.href.split('?')[0];
        window.history.replaceState({}, document.title, cleanUrl);
    }

    // Submit form
    form.addEventListener('submit', (e) => {

        const titolo = form.titolo.value.trim();
        const descrizione = form.descrizione.value.trim();
        const argomento = hiddenArgomento.value.trim();
        const modalita = document.querySelector('input[name="modalita"]:checked')?.value;

        if (!titolo) {
            e.preventDefault();
            toastr.error("Il campo Titolo è obbligatorio.");
            return;
        }

        if (!descrizione) {
            e.preventDefault();
            toastr.error("Il campo Descrizione è obbligatorio.");
            return;
        }

        if (!argomento) {
            e.preventDefault();
            toastr.error("Seleziona un argomento per procedere.");
            return;
        }

        modalitaHidden.value = modalita;
    });

});