from typing import Annotated
from api import API
from fastapi import Depends, Request, HTTPException


async def get_api(request: Request) -> API:
    return request.state.core_api


def validate_code(code: str):
    '''
    Validates code input. Either for a guess or a secret code.
    '''
    if len(code) != 4:
        raise HTTPException(status_code=400, detail=f"Invalid code: {code}. Code must be 4 digits")
    if len(set(code)) != 4:
        raise HTTPException(
            status_code=400, detail=f"Invalid code: {code}. Code must contain 4 unique digits.")
    if not code.isdigit():
        raise HTTPException(
            status_code=400, detail=f"Invalid code: {code}. Code must contain only digits")


ApiType = Annotated[API, Depends(get_api)]
