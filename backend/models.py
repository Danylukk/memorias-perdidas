from pydantic import BaseModel, ConfigDict, Field


class GenerationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instructions: str = Field(min_length=1, max_length=12000)
    context: str = Field(min_length=1, max_length=30000)
    response_schema: dict | None = None
    max_output_tokens: int = Field(default=512, ge=1, le=1600)


class GenerationOutput(BaseModel):
    texto: str = Field(min_length=1)
