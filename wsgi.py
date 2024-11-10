import os
from jat import app
from dotenv import load_dotenv

#print(f".env Path: {os.getenv('FLASK_ENV')}") 

# Load .env only in development
if os.getenv("FLASK_ENV") == "development":
    load_dotenv()

#print("Loaded Environment Variables:")
#for key, value in os.environ.items():
    #print(f"{key}={value}")
   
if __name__ == "__main__":
    app.run()