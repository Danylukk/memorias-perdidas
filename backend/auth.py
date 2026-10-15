import secrets
from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(request: Request, key: str | None = Security(api_key_header)):
    expected = request.app.state.settings.access_key
    if not expected:
        raise HTTPException(status_code=503, detail="API sem credencial de acesso configurada.")
    if not key or not secrets.compare_digest(key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Credencial de acesso inválida.")
