from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Business Cards Simple", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "business_cards_simple"}

@app.get("/test")  
def test():
    return {"message": "Simple service OK", "status": "working"}

if __name__ == "__main__":
    print("🚀 Starting simple service on port 8991...")
    uvicorn.run(app, host="0.0.0.0", port=8991)
