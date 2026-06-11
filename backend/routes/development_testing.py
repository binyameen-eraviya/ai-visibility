from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["test"])

@router.post("/development-test")
def test():
    return "success"

@router.post("/development-test2")
def test1():
    return "success"


@router.post("/development-test3")
def test2():
    return "success"