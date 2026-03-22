from fastapi import APIRouter, Depends, Header, HTTPException


def verify_admin_key(x_api_key: str = Header(...)):
    # client must send header: X-API-Key: eco_admin_secret
    if x_api_key != "eco_admin_secret":
        raise HTTPException(status_code=403, detail="Invalid Key")


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin_key)],  # <-- applies to ALL endpoints here
)


@router.get("/stats")
def get_stats():
    return "Admin stats secured"