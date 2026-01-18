import httpx
from fastapi import Request, HTTPException, status
from fastapi.responses import Response


async def proxy_request(
    service_url: str,
    path: str,
    method: str,
    request: Request,
    headers: dict = None
):
    """İsteği ilgili servise yönlendir"""
    url = f"{service_url}{path}"

    # Query parametrelerini al
    query_params = dict(request.query_params)

    # Body'yi al (varsa)
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
        except Exception:
            body = None

    # Orijinal header'ları kopyala (Host ve Content-Length hariç)
    forward_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    
    # Client IP'sini X-Forwarded-For header'ına ekle (eğer yoksa)
    if request.client and request.client.host:
        client_ip = request.client.host
        existing_forwarded = forward_headers.get("X-Forwarded-For")
        if existing_forwarded:
            # Varsa başına ekle
            forward_headers["X-Forwarded-For"] = f"{client_ip}, {existing_forwarded}"
        else:
            # Yoksa oluştur
            forward_headers["X-Forwarded-For"] = client_ip

    # Ekstra header'lar verildiyse uygula
    if headers:
        forward_headers.update(headers)

    # Authorization header'ı ekle (varsa)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        forward_headers["Authorization"] = auth_header

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                params=query_params,
                content=body,
                headers=forward_headers
            )

            # Hop-by-hop header'ları çıkar
            excluded_headers = {"content-encoding", "transfer-encoding", "connection"}
            headers_to_send = {
                key: value
                for key, value in response.headers.items()
                if key.lower() not in excluded_headers
            }

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=headers_to_send,
                media_type=response.headers.get("content-type")
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}"
        )
