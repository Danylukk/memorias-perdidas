from fastapi import APIRouter, Depends, HTTPException, Request
from backend.auth import require_api_key
from backend.config import ConfigurationError
from backend.models import GenerationInput, GenerationOutput
from backend.providers.openai_provider import AIClientError

router = APIRouter(prefix="/v1/ia-generativa", tags=["IA generativa"],
                   dependencies=[Depends(require_api_key)])


@router.post("/texto", response_model=GenerationOutput)
def generate_text(entrada: GenerationInput, request: Request):
    """Gera falas e lembranças do MVP por meio do provider do grupo."""
    try:
        text = request.app.state.provider.generate(entrada)
    except ConfigurationError:
        raise HTTPException(status_code=503, detail="IA não configurada no backend.") from None
    except AIClientError:
        raise HTTPException(status_code=502, detail="IA generativa indisponível.") from None
    return GenerationOutput(texto=text)
