from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_client_ip(request: Request) -> str:
    # Se estiver atrás de proxy (nginx), pode vir em X-Forwarded-For
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # pega o primeiro IP da lista
        return xff.split(",")[0].strip()

    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)
