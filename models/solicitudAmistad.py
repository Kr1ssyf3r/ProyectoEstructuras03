from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4
#representa una petición que todavía no se ha convertido en una conexión.
#uso de dataclass para representar una solicitud de amistad, DRY
#validaciones en el post_init para asegurar que los ids sean UUID v4 canónicos
#fecha de envío sea válida.

@dataclass(frozen=True) #el frozen es para que no se pueda modificar la soli, la unica forma es que el gestor de solicitudes la elimine y ya
#los fields default_factory son para que se generen automaticamente el id de la solicitud y la fecha de envio
class SolicitudAmistad:
    id_emisor: str
    id_receptor: str
    id_solicitud: str = field(default_factory=lambda: str(uuid4()))
    fecha_envio: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


    def __post_init__(self):
        for nombre in ("id_solicitud", "id_emisor", "id_receptor"):
            valor = getattr(self, nombre) #obtiene el valor del atributo de la instancia actual, es decir self.id_solicitud, self.id_emisor, self.id_receptor

            if not isinstance(valor, str):
                raise ValueError(f"{nombre} debe ser texto UUID.")

            try:
                identificador = UUID(valor)
            except ValueError as error:
                raise ValueError(
                    f"{nombre} debe ser UUID v4 canónico."
                ) from error

            if identificador.version != 4 or str(identificador) != valor:
                raise ValueError(f"{nombre} debe ser UUID v4 canónico.")
            
        if self.id_emisor == self.id_receptor:
            raise ValueError("No se puede enviar una solicitud a uno mismo.")

        try:
            fecha = datetime.fromisoformat(self.fecha_envio)
        except (ValueError, TypeError) as error:
            raise ValueError("Fecha de solicitud inválida.") from error

        if fecha.tzinfo is None:
            raise ValueError("La fecha de la solicitud debe incluir zona horaria.")

    def to_dict(self) -> dict:
        return {
            "id_solicitud": self.id_solicitud,
            "id_emisor": self.id_emisor,
            "id_receptor": self.id_receptor,
            "fecha_envio": self.fecha_envio,}

    @classmethod
    def from_dict(cls, datos: dict):
        claves = {"id_solicitud", "id_emisor", "id_receptor", "fecha_envio"}

        if not isinstance(datos, dict) or set(datos) != claves:
            raise ValueError("Solicitud con formato inválido.")

        return cls(**datos)