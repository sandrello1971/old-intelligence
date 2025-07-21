from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Business Cards 8992", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "business_cards", "port": 8992}

@app.get("/test")  
def test():
    return {"message": "Service OK on 8992", "status": "working"}

if __name__ == "__main__":
    print("🚀 Starting on port 8992...")
    uvicorn.run(app, host="0.0.0.0", port=8992)
