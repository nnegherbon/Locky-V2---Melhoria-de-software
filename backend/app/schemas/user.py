from pydantic import BaseModel, EmailStr

from app.models import Usuario


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    @classmethod
    def from_model(cls, usuario: Usuario) -> "UserResponse":
        return cls(
            id=usuario.id,
            name=usuario.nome,
            email=usuario.email,
            role=usuario.papel,
        )
