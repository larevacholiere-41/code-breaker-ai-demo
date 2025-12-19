from typing import Annotated
from api import API
from fastapi import Depends, Request


async def get_api(request: Request) -> API:
    return request.state.core_api


ApiType = Annotated[API, Depends(get_api)]
