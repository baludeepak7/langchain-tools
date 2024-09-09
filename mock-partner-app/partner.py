from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# In-memory database
db = {
    "7636": {
        "id": "7636",
        "name": "uber",
        "ica": "Customer satisfaction score of 4.5 out of 5.",
        "companyId": "637389"
    }
}

# Pydantic model for validation
class BookingPartner(BaseModel):
    id: str
    name: str
    ica: str
    companyId: str

@app.get("/travel/booking-partner/", response_model=List[BookingPartner])
async def get_all_partners():
    return list(db.values())

@app.get("/travel/booking-partner/{partner_id}", response_model=BookingPartner)
async def get_partner(partner_id: str):
    partner = db.get(partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Booking partner not found")
    return partner

@app.post("/travel/booking-partner/", response_model=BookingPartner)
async def create_partner(partner: BookingPartner):
    if partner.id in db:
        raise HTTPException(status_code=400, detail="Booking partner already exists")
    db[partner.id] = partner.dict()
    return partner

@app.put("/travel/booking-partner/{partner_id}", response_model=BookingPartner)
async def update_partner(partner_id: str, partner: BookingPartner):
    if partner_id not in db:
        raise HTTPException(status_code=404, detail="Booking partner not found")
    db[partner_id] = partner.dict()
    return partner

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9097)
