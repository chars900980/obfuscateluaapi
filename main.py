from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import uuid
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://duckxh4101.x10.bz/obfuscatelua/", "https://hitasroblox.com/"],
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

def add_security_code(original_code):
    security_code = """
local _G, rawget, rawset, error, math, string, pcall, time = _G, rawget, rawset, error, math, string, pcall, os.time or function() return 0 end

-- Key động và mã hóa
local function gen_key(code) local k="s_"..math.random(1e4,9e4)..(time()%1e3);local h=0;for i=1,#code do h=h+string.byte(code,i)*(i%7)end;return k..(h%1e4)end
local function enc(s,k) local r="";for i=1,#s do r=r..string.char((string.byte(s,i)+string.byte(k,i%#k+1))%256)end return r end
local function dec(e,k) local r="";for i=1,#e do r=r..string.char((string.byte(e,i)-string.byte(k,i%#k+1))%256)end return r end

-- Kiểm tra cơ bản
local function chk_prnt() local s,e=pcall(function() print("v")end);if not s then error("Print tampered!")end end
local function chk_env() local t=math.random(1e3,9e3);rawset(_G,t,true);if not rawget(_G,t)then error("Env tampered!")end;rawset(_G,t,nil)end
local function chk_time() local s=time();local r=math.random(3e3,7e3);for i=1,r do math.random()end;local d=time()-s;if d>3 then error("Time anomaly! Debugger detected!")end end
local function self_chk() local f=loadstring("local x=42;return x");if not f or f()~=42 then error("Integrity fail!")end end

-- Kiểm tra môi trường Roblox
local function is_roblox_env()
    local s,e=pcall(function() return _G.game and _G.game.Players and _G.game:GetService("RunService") end)
    return s and e
end

-- Anti-debug
local function chk_debugger()
    local s,e=pcall(function() return debug end);if s and e then error("Debugger detected!")end
    local t1=time();for i=1,1e3 do local x=math.random()end;local t2=time();if t2-t1>1 then error("Debug timing anomaly!")end
end

-- Anti-spy
local function chk_spy()
    local orig_getfenv=getfenv;local s,e=pcall(function() getfenv=function() end end);if s then error("Spy detected: getfenv tampered!")end
    local orig_setfenv=setfenv;local s2,e2=pcall(function() setfenv=function() end end);if s2 then error("Spy detected: setfenv tampered!")end
    local orig_getmetatable=getmetatable;local s3,e3=pcall(function() getmetatable=function() end end);if s3 then error("Spy detected: getmetatable tampered!")end
    local accesses=0;local mt={__index=function(t,k) accesses=accesses+1;if accesses>100 then error("Spy detected: Excessive _G access!")end;return rawget(t,k)end};setmetatable(_G,mt)
end

-- Kiểm tra skidder
local function is_skidder()
    if not is_roblox_env() then return false end
    local orig_print=print;local test="test";local s,e=pcall(function() print=test end);if s then return true end
    local orig_tostring=tostring;local test_val="test_val";if tostring(test_val)~=orig_tostring(test_val) then return true end
    return false
end

-- Nuke khi phát hiện skidder
local function nuke()
    print("Skidder detected! Nuking...")
    for i=1,1e13 do print(i) end
    for i=1,1e5 do local x=math.random(1e4);x=x*x*x;end
    error("Script terminated due to unauthorized access!")
end

-- Hàm bảo vệ
local function protect()
    chk_prnt();chk_env();chk_time();self_chk();chk_debugger();chk_spy()
    if is_skidder() then nuke() end
    local k=gen_key("code_ver");local e=enc("script obfuscated by ducknovis",k);local d=dec(e,k);print(d)
    if math.random(1,1000)==42 then error("Random check failed!")end
end

-- 1000 hàm giả với nội dung giả
local fake=""
for i=1,1000 do
    local name
    if i%3==0 then
        name=({"autofarm","autobuy","autosell","autoquest","autoloot","autoupgrade","autospin","autotrade","autofish","autoboss",
               "autoclick","autodrop","autopick","autolevel","autohit","autofly","autokill","autobuff","autoboost","autospeed",
               "autogold","autogem","autopoint","autoevent","autotask","autowin","autobattle","autodefend","autocollect","autopet"})[math.random(1,30)]
    else
        name="rnd_"..string.char(math.random(97,122))..math.random(1e3,9e3)
    end
    local var="v"..math.random(1e3,9e3)
    fake=fake.."local function "..name.."_"..var.."() local x="..math.random(1e4)..";for i=1,"..math.random(10,50).." do x=x+"..math.random(1,100)..";end;local y=game.Players.LocalPlayer;local z=y and y.Character and y.Character:FindFirstChild('Humanoid');if z then z.WalkSpeed="..math.random(16,100)..";end;return x end;"..name.."_"..var.."();"
end

-- Thực thi
fake=gen_key(fake)..fake
protect()
"""

    return security_code + "\n" + original_code

@app.post("/obfuscate")
async def obfuscate_lua_code(lua_code: LuaCode):
    try:
        secured_code = add_security_code(lua_code.code)
        input_filename = get_next_filename()
        with open(input_filename, "w", encoding="utf-8") as f:
            f.write(secured_code)
        output_filename = f"{input_filename.split('.')[0]}.obfuscated.lua"
        command = ["lua5.3", "./cli.lua", "--preset", "Medium", input_filename]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Obfuscation failed: {e.stderr}")
        if not os.path.exists(output_filename):
            raise HTTPException(status_code=500, detail="Obfuscated file not found")
        with open(output_filename, "r", encoding="utf-8") as f:
            obfuscated_code = f.read()
        final_obfuscated_code = "-- script obfuscated by ducknovis\n" + obfuscated_code
        os.remove(input_filename)
        os.remove(output_filename)
        return {"obfuscated_code": final_obfuscated_code}
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))