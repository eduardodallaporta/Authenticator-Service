from pydantic import BaseModel, Field


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        description="Refresh token (string) recebido no login/refresh. Envie exatamente como retornado pela API.",
        examples=["string_refresh_token_aqui"],
        min_length=20,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"refresh_token": "string_refresh_token_aqui"},
            ]
        }
    }


class TokenResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT de acesso. Use em 'Authorization: Bearer <access_token>'.",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo do token para o header Authorization.",
        examples=["bearer"],
    )
    refresh_token: str = Field(
        ...,
        description="Refresh token (string). Guarde com segurança; será usado para /auth/refresh e /auth/logout.",
        examples=["string_refresh_token_aqui"],
    )
    expires_in: int = Field(
        ...,
        description="Tempo de expiração do access token em segundos.",
        examples=[900],
        ge=1,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "refresh_token": "string_refresh_token_aqui",
                    "expires_in": 900,
                }
            ]
        }
    }
