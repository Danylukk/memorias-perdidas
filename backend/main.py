from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import Settings
from backend.providers.openai_provider import OpenAIProvider
from backend.routers.ia_generativa import router


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    application = FastAPI(title="Memórias Perdidas — API do grupo", version="1.0.0")
    application.state.settings = settings
    application.state.provider = OpenAIProvider(settings)
    # Pygame/requests não exige CORS. Origens web são opcionais e explícitas.
    application.add_middleware(
        CORSMiddleware, allow_origins=list(settings.cors_origins),
        allow_methods=["POST"], allow_headers=["Content-Type", "X-API-Key"],
    )
    application.include_router(router)
    return application


app = create_app()
