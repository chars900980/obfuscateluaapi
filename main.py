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
local _G, rawget, rawset, error, math, string, pcall, time = _G, rawget, rawset, error, math, string, pcall, os.time or function() return 0 end

-- Key động và mã hóa
local function gen_key(code) local k="s_"..math.random(1e4,9e4)..(time()%1e3);local h=0;for i=1,#code do h=h+string.byte(code,i)*(i%7)end;return k..(h%1e4)end
local function enc(s,k) local r="";for i=1,#s do r=r..string.char((string.byte(s,i)+string.byte(k,i%#k+1))%256)end return r end
local function dec(e,k) local r="";for i=1,#e do r=r..string.char((string.byte(e,i)-string.byte(k,i%#k+1))%256)end return r end

-- Kiểm tra cơ bản
local function chk_prnt() local s,e=pcall(function() print("v")end);if not s then error("Print tampered!")end end
local function chk_env() local t=math.random(1e3,9e3);rawset(_G,t,true);if not rawget(_G,t)then error("Env tampered!")end;rawset(_G,t,nil)end
local function chk_time() local s=time();for i=1,5e3 do math.random()end;if time()-s>5 then error("Time anomaly!")end end
local function self_chk() local f=loadstring("local x=42;return x");if not f or f()~=42 then error("Integrity fail!")end end

-- Kiểm tra chống skidder
local function chk_debug() if debug and debug.getinfo then error("Debugger detected! Script nuked.") end end
local function chk_hook() if hook and hookmetamethod then error("Hook detected! Script nuked.") end end
local function chk_stack() local s=0;for k,v in pairs(debug and debug.getstack or {})do s=s+1 end;if s>10 then error("Stack tampered! Script nuked.")end end

-- Hàm bảo vệ
local function protect() chk_prnt();chk_env();chk_time();self_chk();chk_debug();chk_hook();chk_stack()
    local k=gen_key("code_ver");local e=enc("script obfuscated by ducknovis",k);local d=dec(e,k);print(d)
    if math.random(1,100)==42 then error("Random nuke triggered!") end
end

-- 100 hàm giả ngẫu nhiên gây chú ý
local fake=""
for i=1,100 do
    local name=({"autofarm","autobuy","autosell","autoquest","autoloot","autoupgrade","autospin","autotrade","autofish","autoboss",
                "autoclick","autodrop","autopick","autolevel","autohit","autofly","autokill","autobuff","autoboost","autospeed",
                "autogold","autogem","autopoint","autoevent","autotask","autowin","autobattle","autodefend","autocollect","autopet",
                "autohack","autodamage","autoshield","autofreeze","autolock","autounlock","autosave","autoload","autocheat",
                "autowarp","autoport","autotele","autoblock","autounblock","autofire","autoheal","autopower","autodefense",
                "autostrike","autoblast","autoshot","autolaunch","autododge","autoevasion","autoshieldup","autobreak","autofix",
                "autoreset","autoreload","autobackup","autorest","autofocus","autotrack","autotarget","autolaser","autobeam",
                "autodrive","autoforge","autosmelt","autocraft","autobuild","autodestroy","autodelete","autofusion","autoevolve",
                "autotransform","autoupdate","autodownload","autoupload","autodeploy","autowork","autofeed","autoharvest",
                "autoplant","autowater","autofence","autoguard","autopatrol","autoscout","autosnipe","autobomb","autoblast",
                "autodetonate","autotrigger","autoactivate","autodeactivate","autolimit","autounlimit"})[math.random(1,70)]
    local var="v"..math.random(1e3,9e3)
    fake=fake.."local function "..name.."_"..var.."()local x="..math.random(1e4)..";return x*"..math.random(1,100).."end;"..name.."_"..var.."();"
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