from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import uuid

app = FastAPI()

# Thêm middleware CORS với origin cụ thể
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://duckxh4101.x10.bz/obfuscatelua/"],  # Chỉ cho phép origin này
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả method (GET, POST, v.v.)
    allow_headers=["*"],  # Cho phép tất cả header
)

# Định nghĩa model cho dữ liệu đầu vào
class LuaCode(BaseModel):
    code: str

def get_next_filename(base_name="new", extension=".lua"):
    """Tìm tên file tiếp theo (new.lua, new1.lua, new2.lua, ...)"""
    counter = 0
    while True:
        filename = f"{base_name}{'' if counter == 0 else counter}{extension}"
        if not os.path.exists(filename):
            return filename
        counter += 1

@app.post("/obfuscate")
async def obfuscate_lua_code(lua_code: LuaCode):
    try:
        # Lấy tên file mới
        input_filename = get_next_filename()
        
        # Ghi mã Lua vào file
        with open(input_filename, "w", encoding="utf-8") as f:
            f.write(lua_code.code)
        
        # Chạy lệnh obfuscation
        output_filename = f"{input_filename.split('.')[0]}.obfuscated.lua"
        command = ["lua5.3", "./cli.lua", "--preset", "Medium", input_filename]
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Obfuscation failed: {e.stderr}")
        
        # Đọc nội dung file đã obfuscate
        if not os.path.exists(output_filename):
            raise HTTPException(status_code=500, detail="Obfuscated file not found")
            
        with open(output_filename, "r", encoding="utf-8") as f:
            obfuscated_code = f.read()
        
        # Xóa các file tạm
        os.remove(input_filename)
        os.remove(output_filename)
        
        return {"obfuscated_code": obfuscated_code}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))