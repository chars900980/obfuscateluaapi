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

# Hàm thêm mã bảo mật vào script
def add_security_code(original_code):
    security_code = """
local function super_encrypt(str, key)
    local result = ""
    local key_hash = 0 for i = 1, #key do key_hash = key_hash + key:byte(i) end
    for i = 1, #str do
        local b = str:byte(i)
        local k = key:byte((i % #key) + 1)
        local shift = (key_hash % 8) + 1
        result = result .. string.char(bit32.bxor(b, k) ~ (i % 255) + bit32.rshift(b, shift))
    end
    return result
end

local function super_decrypt(enc, key)
    local result = ""
    local key_hash = 0 for i = 1, #key do key_hash = key_hash + key:byte(i) end
    for i = 1, #enc do
        local b = enc:byte(i)
        local k = key:byte((i % #key) + 1)
        local shift = (key_hash % 8) + 1
        local xored = bit32.bxor(b - bit32.rshift(enc:byte(i), shift), k)
        result = result .. string.char(xored ~ (i % 255))
    end
    return result
end

local function check_timing_advanced()
    local times = {}
    for _ = 1, 5 do
        local start = os.clock()
        local dummy = 0
        for i = 1, math.random(2000, 8000) do
            dummy = dummy + math.tan(math.random()) * math.log(i + 1)
        end
        times[#times + 1] = os.clock() - start
    end
    local avg = 0 for _, t in ipairs(times) do avg = avg + t end avg = avg / #times
    if avg > 0.02 or math.abs(times[1] - times[#times]) > 0.01 then
        error("Advanced timing anomaly detected!")
    end
end

local function check_debug_advanced()
    if debug.gethook() then
        error("Debug hook detected!")
    end
    local mt = getmetatable(_G) or getmetatable(function() end)
    if mt and (mt.__index or mt.__newindex) then
        error("Metatable tampering detected!")
    end
end

local function check_stack_advanced()
    local level = 1
    local count = 0
    local last_line = -1
    while true do
        local info = debug.getinfo(level, "Sln")
        if not info then break end
        if info.currentline == last_line and last_line ~= -1 then
            error("Suspicious stack line repetition detected!")
        end
        last_line = info.currentline
        count = count + 1
        level = level + 1
    end
    if count > 15 then
        error("Excessive stack depth detected!")
    end
end

local function check_env_advanced()
    local orig_tostring = tostring
    if _G.tostring ~= orig_tostring or _G.print ~= print then
        error("Global environment tampering detected!")
    end
    local test = function() end
    if string.dump(test) == string.dump(function() end) then
        error("Function cloning detected!")
    end
end

local function check_memory_tamper()
    local secret = math.random(1, 1000000)
    local function guard()
        if secret ~= math.random(1, 1000000) then
            error("Memory tampering detected!")
        end
    end
    for i = 1, 100 do
        guard()
        secret = math.random(1, 1000000)
    end
end

local function check_bytecode_advanced()
    local func = function() print("Critical logic") end
    local bytecode = string.dump(func)
    local checksum = 0
    for i = 1, #bytecode do
        checksum = checksum + (bytecode:byte(i) * (i % 17))
    end
    if checksum % 65536 ~= 54321 then
        error("Advanced bytecode tampering detected!")
    end
end

local function dynamic_execution()
    local code = super_encrypt("return function() print('Protected logic') end", "superkey987")
    local decrypted_code = super_decrypt(code, "superkey987")
    local func = loadstring(decrypted_code)
    if func then
        local inner = func()
        inner()
    else
        error("Dynamic code execution failed!")
    end
end

local function super_junk()
    local t = {}
    for i = 1, math.random(5000, 15000) do
        t[i] = math.tan(math.random()) * math.log(i + 1)
        if math.fmod(t[i], 3) == 0 then
            t[i] = string.char(math.random(65, 90))
        end
    end
    return function() return t[math.random(1, #t)] end
end

local function protect_code()
    check_timing_advanced()
    check_debug_advanced()
    check_stack_advanced()
    check_env_advanced()
    check_memory_tamper()
    check_bytecode_advanced()
    dynamic_execution()
    super_junk()()
end

-- Gọi hàm bảo vệ
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
        
        # Lấy tên file mới
        input_filename = get_next_filename()
        
        # Ghi mã Lua đã thêm bảo mật vào file
        with open(input_filename, "w", encoding="utf-8") as f:
            f.write(secured_code)
        
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
        
        # Thêm dòng nhận xét vào đầu script đã obfuscate
        final_obfuscated_code = "-- script obfuscated by ducknovis\n" + obfuscated_code
        
        # Xóa các file tạm
        os.remove(input_filename)
        os.remove(output_filename)
        
        return {"obfuscated_code": final_obfuscated_code}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))