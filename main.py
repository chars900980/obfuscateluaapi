from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import uuid
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Hàm thêm mã bảo mật vào script
def add_security_code(original_code):
    security_code = """
local _G = _G
local rawget = rawget
local rawset = rawset
local error = error
local math = math
local string = string
local pcall = pcall

-- Hàm mã hóa đơn giản
local function encrypt(str, key)
    local result = ""
    for i = 1, #str do
        local b = string.byte(str, i)
        local k = string.byte(key, (i - 1) % #key + 1)
        result = result .. string.char((b + k) % 256)
    end
    return result
end

-- Hàm giải mã
local function decrypt(enc, key)
    local result = ""
    for i = 1, #enc do
        local b = string.byte(enc, i)
        local k = string.byte(key, (i - 1) % #key + 1)
        result = result .. string.char((b - k) % 256)
    end
    return result
end

-- Kiểm tra môi trường
local function check_environment()
    local test = {}
    rawset(_G, "test", test)
    if _G.test ~= test then
        error("Global environment tampering detected!")
    end
    if rawget(_G, "print") ~= print then
        error("Print function tampering detected!")
    end
end

-- Kiểm tra proxy/tampering
local function check_proxy()
    local func = function() end
    local mt = {}
    mt.__call = function() error("Proxy detected!") end
    setmetatable(func, mt)
    local status, err = pcall(function() func() end)
    if status then
        error("Proxy check failed!")
    end
end

-- Tạo mã junk để làm khó phân tích
local function generate_junk()
    local junk = ""
    for i = 1, math.random(10, 20) do
        junk = junk .. string.char(math.random(65, 90)) .. " = " .. math.random(1, 1000) .. ";"
    end
    return junk
end

-- Hàm bảo vệ chính
local function protect_code()
    check_environment()
    check_proxy()
    local key = "securekey_" .. math.random(1000, 9999)
    local enc = encrypt("Protected", key)
    local dec = decrypt(enc, key)
    if dec ~= "Protected" then
        error("Encryption integrity check failed!")
    end
end

-- Thêm mã junk và bảo vệ
local junk = generate_junk()
protect_code()

-- Thêm mã chính của người dùng ở đây
"""

    # Kết hợp mã bảo mật với mã của người dùng
    combined_code = security_code + "\n" + original_code
    return combined_code

@app.post("/obfuscate")
async def obfuscate_lua_code(lua_code: LuaCode):
    try:
        # Thêm mã bảo mật vào script nhận được
        secured_code = add_security_code(lua_code.code)
        logger.info(f"Secured code length: {len(secured_code)}")
        
        # Lấy tên file mới
        input_filename = get_next_filename()
        
        # Ghi mã Lua đã thêm bảo mật vào file
        with open(input_filename, "w", encoding="utf-8") as f:
            f.write(secured_code)
        logger.info(f"Written to file: {input_filename}")
        
        # Chạy lệnh obfuscation
        output_filename = f"{input_filename.split('.')[0]}.obfuscated.lua"
        command = ["lua5.3", "./cli.lua", "--preset", "Medium", input_filename]
        logger.info(f"Executing command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Obfuscation command executed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Obfuscation failed: {e.stderr}")
            raise HTTPException(status_code=500, detail=f"Obfuscation failed: {e.stderr}")
        
        # Đọc nội dung file đã obfuscate
        if not os.path.exists(output_filename):
            logger.error(f"Obfuscated file not found: {output_filename}")
            raise HTTPException(status_code=500, detail="Obfuscated file not found")
            
        with open(output_filename, "r", encoding="utf-8") as f:
            obfuscated_code = f.read()
        
        # Thêm dòng nhận xét vào đầu script đã obfuscate
        final_obfuscated_code = "-- script obfuscated by ducknovis\n" + obfuscated_code
        
        # Xóa các file tạm
        os.remove(input_filename)
        os.remove(output_filename)
        
        return {"obfuscated_code": final_obfuscated_code}
    
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))