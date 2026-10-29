from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.exceptions import CredenciaisInvalidasError
from app.core.security import decodificar_token
from app.models import PapelUsuario, Usuario
from app.repositories import usuario_repository

seguranca = HTTPBearer(auto_error=False)


def _nao_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(seguranca)],
) -> Usuario:
    if credenciais is None:
        raise _nao_autenticado()

    try:
        usuario_id = decodificar_token(credenciais.credentials)
    except CredenciaisInvalidasError:
        raise _nao_autenticado() from None

    usuario = usuario_repository.buscar_por_id(session, usuario_id)
    if usuario is None:
        raise _nao_autenticado()
    return usuario


def require_admin(
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> Usuario:
    """Autorização no servidor: esconder o menu no frontend não protege a API."""
    if usuario.papel != PapelUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return usuario
