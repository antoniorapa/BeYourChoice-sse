import os
import re
import uuid
from bson import ObjectId
from flask import flash, redirect, url_for, send_file, abort, session , request
from app.models.materialeModel import MaterialeModel

MAX_FILE_SIZE_MB = 2
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'jpeg', 'png', 'txt', 'jpg', 'mp4'}

TITOLO_RE = re.compile(r'^[A-Za-z0-9 ]{2,20}$')
DESCRIZIONE_RE = re.compile(r'^[^§]{2,255}$')


class MaterialeControl:
    def __init__(self, db_manager,cartella_uploads=None):
        self.control = MaterialeModel(db_manager)
        self.cartella_uploads = cartella_uploads

    def set_cartella_uploads(self, path_cartella):
        self.cartella_uploads = path_cartella

    def titolo_valido(self, titolo):
        return bool(TITOLO_RE.match(titolo or ""))

    def descrizione_valida(self, descrizione):
        return bool(DESCRIZIONE_RE.match(descrizione or ""))

    def tipo_file_valido(self, nome_file):
        if not nome_file or '.' not in nome_file:
            return False
        return nome_file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def grandezza_file_valida(self, file):
        # content_length può essere None in alcuni casi: gestiamo
        size = getattr(file, "content_length", None)
        if size is None:
            return True  # fallback: non blocchiamo, ma potresti volerlo rendere False
        return size <= MAX_FILE_SIZE_MB * 1024 * 1024

    def _require_upload_folder(self):
        if not self.cartella_uploads:
            raise RuntimeError("Cartella uploads non configurata")
        os.makedirs(self.cartella_uploads, exist_ok=True)

    def carica_materiale(self, request):
        titolo = request.form.get('titolo', '')
        descrizione = request.form.get('descrizione', '')
        tipo = request.form.get('tipo', '')
        file = request.files.get('file')
        id_classe = session.get('id_classe')

        if not file:
            flash("File mancante.", "error")
            return redirect(request.url)

        if not self.titolo_valido(titolo):
            flash("Titolo non valido (2-20, solo lettere/numeri/spazi).", "error")
            return redirect(request.url)

        if not self.descrizione_valida(descrizione):
            flash("Descrizione non valida (2-255).", "error")
            return redirect(request.url)

        if not self.tipo_file_valido(file.filename):
            flash("Tipo file non valido.", "error")
            return redirect(request.url)

        file_extension = file.filename.rsplit('.', 1)[1].lower()
        if tipo != file_extension:
            flash("Tipo selezionato non corrisponde all'estensione.", "error")
            return redirect(request.url)

        if not self.grandezza_file_valida(file):
            flash(f"File troppo grande (max {MAX_FILE_SIZE_MB} MB).", "error")
            return redirect(request.url)

        self._require_upload_folder()

        # nome file “safe”: manteniamo solo basename
        safe_name = os.path.basename(file.filename)
        file.save(os.path.join(self.cartella_uploads, safe_name))

        nuovo_materiale = {
            "id_materiale": uuid.uuid4().hex,
            "titolo": titolo,
            "descrizione": descrizione,
            "file_path": safe_name,
            "tipo": tipo,
            "id_classe": id_classe
        }
        self.control.carica_materiali(nuovo_materiale)

        flash("Materiale caricato con successo!", "materiale_success")
        return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

    def modifica_materiale(self, id_materiale, request):
        try:
            id_materiale_obj = ObjectId(id_materiale)
        except Exception:
            flash("ID materiale non valido.", "error")
            return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

        materiale = self.control.get_materiale_tramite_id(id_materiale_obj)
        if materiale is None:
            flash("Materiale non trovato.", "error")
            return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

        if request.method == 'POST':
            titolo = request.form.get('titolo', '')
            descrizione = request.form.get('descrizione', '')

            if not self.titolo_valido(titolo):
                flash("Titolo non valido.", "error")
                return redirect(request.url)

            if not self.descrizione_valida(descrizione):
                flash("Descrizione non valida.", "error")
                return redirect(request.url)

            file = request.files.get('file')
            if file and file.filename:
                if not self.tipo_file_valido(file.filename):
                    flash("Tipo file non valido.", "error")
                    return redirect(request.url)

                if not self.grandezza_file_valida(file):
                    flash(f"File troppo grande (max {MAX_FILE_SIZE_MB} MB).", "error")
                    return redirect(request.url)

                self._require_upload_folder()
                safe_name = os.path.basename(file.filename)
                file.save(os.path.join(self.cartella_uploads, safe_name))
                materiale['file_path'] = safe_name

            dati_caricati = {
                "titolo": titolo,
                "descrizione": descrizione,
                "file_path": materiale.get('file_path')
            }

            self.control.modifica_materiale(id_materiale_obj, dati_caricati)
            flash("Materiale modificato con successo!", "materiale_success")
            return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

    def rimuovi_materiale(self, id_materiale):
        try:
            id_materiale_obj = ObjectId(id_materiale)
        except Exception as e:
            flash(f"ID non valido: {e}", "error")
            return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

        materiale = self.control.visualizza_materiale({"_id": id_materiale_obj})
        if materiale is None:
            flash("Materiale non trovato.", "error")
            return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

        if not self.control.elimina_materiale(id_materiale_obj):
            flash("Errore rimozione dal DB.", "error")
            return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

        file_path = materiale.get('file_path')
        if file_path and self.cartella_uploads:
            full_path = os.path.join(self.cartella_uploads, file_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except OSError as e:
                    flash(f"Errore eliminazione file: {e}", "error")

        flash("Materiale rimosso con successo!", "materiale_success")
        return redirect(url_for('MaterialeDocente.visualizza_materiale_docente'))

    def visualizza_materiali(self, id_classe):
        return self.control.get_materiali_tramite_id_classe(id_classe)

    def servi_file(self, nome_file):
        if not self.cartella_uploads:
            abort(500)

        safe_name = os.path.basename(nome_file)
        file_path = os.path.join(self.cartella_uploads, safe_name)

        if os.path.exists(file_path):
            return send_file(file_path)
        abort(404)
