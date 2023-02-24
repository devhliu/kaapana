from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")
async def root(request: Request):
    return {"message": "Welcome to the backend", "root_path": request.scope.get("root_path")}


@router.get("/health-check")
def health_check():
    return {f"Kaapana backend is up and running!"}
