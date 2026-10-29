from pydantic import BaseModel, EmailStr, Field

# bcrypt só considera os primeiros 72 bytes da senha; acima disso o restante
# seria ignorado silenciosamente, então limitamos explicitamente.
SENHA_TAMANHO_MINIMO = 6
SENHA_TAMANHO_MAXIMO = 72


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(
        min_length=SENHA_TAMANHO_MINIMO, max_length=SENHA_TAMANHO_MAXIMO
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
