import json
import os

from pathlib import Path

from models.token_recuperacion import TokenRecuperacion


class TokenRepository:
    """
    Administra el almacenamiento y la consulta de tokens de recuperación.

    Utiliza un diccionario en memoria y un archivo JSON como persistencia.
    """

    def __init__(self, ruta="data/tokens_recuperacion.json"):
        self.ruta = Path(ruta)

        # Diccionario que almacena los tokens identificados por su ID.
        self.tokens_por_id = {}

        self.cargar_tokens()

    def cargar_tokens(self):
        """Carga los tokens desde el archivo JSON."""

        self.tokens_por_id.clear()

        # Si el archivo todavía no existe, no hay tokens que cargar.
        if not self.ruta.exists():
            return

        try:
            with open(self.ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            for elemento in datos:
                token = TokenRecuperacion.from_dict(elemento)
                self.tokens_por_id[token.id] = token

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"No se pudieron cargar los tokens: {error}"
            ) from error

    def guardar_tokens(self):
        """Guarda todos los tokens en el archivo JSON."""

        # Crear la carpeta si todavía no existe.
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

        datos = [
            token.to_dict()
            for token in self.tokens_por_id.values()
        ]

        ruta_temporal = self.ruta.with_suffix(
            self.ruta.suffix + ".tmp"
        )

        try:
            with open(ruta_temporal, "w", encoding="utf-8") as archivo:
                json.dump(
                    datos,
                    archivo,
                    ensure_ascii=False,
                    indent=4
                )

            # Reemplazar el archivo original de forma atómica.
            os.replace(ruta_temporal, self.ruta)

        except OSError:
            if ruta_temporal.exists():
                ruta_temporal.unlink()
            raise

    def guardar(self, token: TokenRecuperacion):
        """Registra un token nuevo o actualiza uno existente."""

        if not isinstance(token, TokenRecuperacion):
            raise TypeError(
                "El objeto debe ser de tipo TokenRecuperacion."
            )

        token_anterior = self.tokens_por_id.get(token.id)

        self.tokens_por_id[token.id] = token

        try:
            self.guardar_tokens()
        except OSError:
            # Restaurar el estado anterior si falla la persistencia.
            if token_anterior is None:
                del self.tokens_por_id[token.id]
            else:
                self.tokens_por_id[token.id] = token_anterior

            raise

    def buscar_por_id(self, id_token: str):
        """Busca un token mediante su identificador."""

        return self.tokens_por_id.get(id_token)

    def buscar_por_hash(self, token_hash: str):
        """Busca un token mediante el hash del token original."""

        for token in self.tokens_por_id.values():
            if token.token_hash == token_hash:
                return token

        return None

    def obtener_por_usuario(self, usuario_id: str) -> list:
        """Obtiene todos los tokens asociados a un usuario."""

        return [
            token
            for token in self.tokens_por_id.values()
            if token.usuario_id == usuario_id
        ]

    def obtener_todos(self) -> list:
        """Devuelve todos los tokens almacenados."""

        return list(self.tokens_por_id.values())

    def eliminar(self, id_token: str):
        """Elimina un token mediante su identificador."""

        token = self.tokens_por_id.get(id_token)

        if token is None:
            return False

        del self.tokens_por_id[id_token]

        try:
            self.guardar_tokens()
        except OSError:
            # Restaurar el token si falla la persistencia.
            self.tokens_por_id[id_token] = token
            raise

        return True