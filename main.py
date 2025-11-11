import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import db, create_document, get_documents
from schemas import Product, Order, OrderItem

app = FastAPI(title="Chibi Maruko Bento API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Chibi Maruko Bento Backend Ready"}

@app.get("/api/hello")
def hello():
    return {"message": "Welcome to Chibi Maruko Bento API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# Seed some default products if collection is empty
@app.post("/api/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"seeded": False, "message": "Products already exist"}
    default_products = [
        {
            "title": "Sakura Bento",
            "description": "Chicken karaage, tamagoyaki, pickled radish, rice with umeboshi.",
            "price": 6.5,
            "category": "bento",
            "image": "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=1200&auto=format&fit=crop",
            "in_stock": True
        },
        {
            "title": "Teriyaki Bento",
            "description": "Salmon teriyaki, steamed veggies, sesame rice.",
            "price": 7.9,
            "category": "bento",
            "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?q=80&w=1200&auto=format&fit=crop",
            "in_stock": True
        },
        {
            "title": "Vegetarian Bento",
            "description": "Tofu katsu, edamame, seaweed salad, miso veggies.",
            "price": 6.0,
            "category": "bento",
            "image": "https://images.unsplash.com/photo-1604908554027-4d09f32f9f2d?q=80&w=1200&auto=format&fit=crop",
            "in_stock": True
        }
    ]
    for p in default_products:
        create_document("product", p)
    return {"seeded": True, "count": len(default_products)}

@app.get("/api/products", response_model=List[Product])
def list_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    docs = get_documents("product")
    # Map Mongo _id to string id if needed, but response_model will ignore extra fields
    products = []
    for d in docs:
        d.pop("_id", None)
        products.append(Product(**d))
    return products

class CreateOrder(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str | None = None
    address: str
    notes: str | None = None
    items: List[OrderItem]

@app.post("/api/orders")
def create_order(order: CreateOrder):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Calculate total from items
    total = 0.0
    for item in order.items:
        total += item.price * item.quantity
    order_doc = Order(
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        address=order.address,
        notes=order.notes,
        items=order.items,
        total=total
    )
    inserted_id = create_document("order", order_doc)
    return {"success": True, "order_id": inserted_id, "total": total}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
