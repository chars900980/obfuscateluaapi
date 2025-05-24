from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import uuid
import logging
import time

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
local time = os.time or function() return 0 end  -- Hỗ trợ nếu os.time bị chặn

-- Hàm tạo key động phức tạp
local function generate_dynamic_key(code)
    local key = "securekey_" .. math.random(1000, 9999) .. "_" .. (time() % 1000)
    local code_hash = 0
    for i = 1, #code do
        code_hash = code_hash + string.byte(code, i) * (i % 7)
    end
    return key .. "_" .. (code_hash % 10000)
end

-- Hàm mã hóa với key động
local function encrypt(str, key)
    local result = ""
    local key_hash = 0
    for i = 1, #key do key_hash = key_hash + string.byte(key, i) end
    for i = 1, #str do
        local b = string.byte(str, i)
        local k = string.byte(key, (i - 1) % #key + 1)
        result = result .. string.char((b + k + (key_hash % 10)) % 256)
    end
    return result
end

-- Hàm giải mã
local function decrypt(enc, key)
    local result = ""
    local key_hash = 0
    for i = 1, #key do key_hash = key_hash + string.byte(key, i) end
    for i = 1, #enc do
        local b = string.byte(enc, i)
        local k = string.byte(key, (i - 1) % #key + 1)
        result = result .. string.char((b - k - (key_hash % 10)) % 256)
    end
    return result
end

-- Kiểm tra hành vi print an toàn
local function safe_check_print()
    local orig_print = print
    local test_val = "verification"
    local success, err = pcall(function() orig_print(test_val) end)
    if not success or err then
        error("Print function tampering detected!")
    end
end

-- Kiểm tra môi trường động
local function check_dynamic_env()
    local test_key = "test_key_" .. math.random(1000, 9999)
    rawset(_G, test_key, true)
    if not rawget(_G, test_key) then
        error("Dynamic environment tampering detected!")
    end
    rawset(_G, test_key, nil)
end

-- Kiểm tra thời gian chạy bất thường
local function check_execution_time()
    local start = time()
    local dummy = 0
    for i = 1, 5000 do
        dummy = dummy + math.random(1, 100)
    end
    local duration = (time() - start)
    if duration > 5 then
        error("Execution time anomaly detected! Possible debugger active.")
    end
end

-- Tạo mã giả (fake code) để làm khó phân tích
local function generate_fake_code()
    local fake = ""
    for i = 1, math.random(5, 10) do
        local var = string.char(math.random(65, 90)) .. math.random(1, 999)
        fake = fake .. "local " .. var .. " = function() local x = " .. math.random(1, 9999) .. "; return x * 2 end;"
        fake = fake .. var .. "();"
    end
    return fake
end

-- Tự kiểm tra tính toàn vẹn của mã
local function self_integrity_check()
    local code_snippet = "local x = 42; return x"
    local func, err = loadstring(code_snippet)
    if not func then
        error("Code integrity check failed: " .. err)
    end
    local result = func()
    if result ~= 42 then
        error("Code integrity check failed: unexpected result!")
    end
end

-- Hàm bảo vệ chính
local function protect_code()
    safe_check_print()
    check_dynamic_env()
    check_execution_time()
    self_integrity_check()
    
    local key = generate_dynamic_key('code_verification')
    local enc = encrypt("script obfuscated by ducknovis", key)
    local dec = decrypt(enc, key)
    print(dec)
    
    -- Thêm kiểm tra runtime phức tạp
    local function runtime_check()
        local count = 0
        for _ in pairs(_G) do count = count + 1 end
        if count > 150 then
            error("Excessive global variables detected! Possible injection.")
        end
    end
    runtime_check()
end

-- Thêm mã giả và bảo vệ
local fake = generate_fake_code()
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