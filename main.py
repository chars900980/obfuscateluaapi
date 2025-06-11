from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class LuaCode(BaseModel):
    code: str

def get_next_filename(base_name="new", extension=".lua"):
    counter = 0
    while True:
        filename = f"{base_name}{'' if counter == 0 else counter}{extension}"
        if not os.path.exists(filename):
            return filename
        counter += 1

@app.post("/obfuscate")
async def obfuscate_lua_code(lua_code: LuaCode):
    try:
        secured_code = lua_code.code
        input_filename = get_next_filename()
        with open(input_filename, "w", encoding="utf-8") as f:
            f.write(secured_code)

        output_filename = f"{input_filename.split('.')[0]}.obfuscated.lua"
        command = ["lua5.3", "/opt/render/project/src/cli.lua", "--preset", "Medium", "--nocolors", "--LuaU", input_filename]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Obfuscation failed: {e.stderr}")

        if not os.path.exists(output_filename):
            raise HTTPException(status_code=500, detail="Obfuscated file not found")

        with open(output_filename, "r", encoding="utf-8") as f:
            obfuscated_code = f.read()

        final_obfuscated_code = "-- script obfuscated by ducknovis with prometheus\n" + obfuscated_code
        os.remove(input_filename)
        os.remove(output_filename)

        return {"obfuscated_code": final_obfuscated_code}
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Explicitly bind the app to a port so Render detects it
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))