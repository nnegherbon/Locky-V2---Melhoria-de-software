from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import CredenciaisInvalidasError, EmailJaCadastradoError
from app.core.security import hash_senha, verificar_senha
from app.models import PapelUsuario, Usuario
from app.repositories import usuario_repository


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def autenticar(session: Session, email: str, senha: str) -> Usuario:
    usuario = usuario_repository.buscar_por_email(session, normalizar_email(email))
    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        raise CredenciaisInvalidasError
    return usuario


def registrar(session: Session, nome: str, email: str, senha: str) -> Usuario:
    """Cria uma conta de associado.

    O papel é sempre ASSOCIADO: o cadastro é público, então aceitar o papel
    vindo do cliente permitiria que qualquer pessoa se tornasse administradora.
    """
    email_normalizado = normalizar_email(email)
    if usuario_repository.buscar_por_email(session, email_normalizado) is not None:
        raise EmailJaCadastradoError

    usuario = Usuario(
        nome=nome.strip(),
        email=email_normalizado,
        senha_hash=hash_senha(senha),
        papel=PapelUsuario.ASSOCIADO,
    )
    session.add(usuario)
    try:
        session.commit()
    except IntegrityError as exc:
        # Duas requisições simultâneas com o mesmo e-mail: o índice único decide.
        session.rollback()
        raise EmailJaCadastradoError from exc
    session.refresh(usuario)
    return usuario
