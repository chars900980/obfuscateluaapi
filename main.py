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
app.add_middleware(CORSMiddleware, allow_origins=["https://duckxh4101.x10.bz/obfuscatelua/"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
local function gen_key(code, name) local k="s_"..math.random(1e4,9e4)..(time()%1e3);local h=0;for i=1,#code do h=h+string.byte(code,i)*(i%7)end;return k..(h%1e4)end
local function enc1(s,k) local r="";for i=1,#s do r=r..string.char((string.byte(s,i)+string.byte(k,i%#k+1))%256)end return r end
local function enc2(s,k) local r="";for i=1,#s do r=r..string.char((string.byte(s,i)-string.byte(k,i%#k+1)+i%5)%256)end return r end
local function enc3(s,k) local r="";for i=1,#s do r=r..string.char((string.byte(s,i)*2-string.byte(k,i%#k+1))%256)end return r end
local function dec1(e,k) local r="";for i=1,#e do r=r..string.char((string.byte(e,i)-string.byte(k,i%#k+1))%256)end return r end
local function dec2(e,k) local r="";for i=1,#e do r=r..string.char((string.byte(e,i)+string.byte(k,i%#k+1)-i%5)%256)end return r end
local function dec3(e,k) local r="";for i=1,#e do r=r..string.char((string.byte(e,i)/2+string.byte(k,i%#k+1))%256)end return r end
local function chk_prnt() local s,e=pcall(function() print("v")end);if not s then error("Print tampered!")end end
local function chk_env() if not pcall(function() return _G.game end) then error("Invalid env!")end end
local function chk_time() local s=time();for i=1,math.random(5e3,1e4)do math.random()end;if time()-s>5 then error("Time anomaly!")end end
local function gen_fake() local f="";for i=1,math.random(20,40)do local v=string.char(math.random(65,90))..math.random(1e3);f=f.."local "..v.."=function()return"..math.random(1e4).."end;"..v.."();end"return f end
local function chk_sum(c) local s=0;for i=1,#c do s=s+string.byte(c,i)*(i%13)end return s%65536 end
local function self_chk(c) local f=loadstring(c);if not f or f()~=42 then error("Integrity fail!")end end
local function protect(n) chk_prnt();chk_env();chk_time();self_chk("local x=42;return x");local k=gen_key(n,n);local e1=enc1("script obfuscated",k);local e2=enc2(e1,k.."_l2");local e3=enc3(e2,k.."_l3");local d1=dec1(e3,k.."_l3");local d2=dec2(d1,k.."_l2");local d3=dec3(d2,k);print(d3);if math.random(1,100)==42 then error("Rand chk fail!")end end
local f=gen_fake();protect(tostring(math.random(1e5,9e5)))
"""

    return security_code + original_code

@app.post("/obfuscate")
async def obfuscate_lua_code(lua_code: LuaCode):
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