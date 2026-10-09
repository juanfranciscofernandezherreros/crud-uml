from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UsuarioEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=120)
    email: EmailStr

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío")
        return value

class UsuarioSalida(UsuarioEntrada):
    id: int
