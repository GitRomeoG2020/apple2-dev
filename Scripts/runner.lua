-- runner.lua : reusable Apple II test runner for MAME 0.289
-- Load with: mame.exe apple2e ... -autoboot_script ..\Scripts\runner.lua
-- Config: file named by env A2RUN_CFG (default ..\Scripts\runner_cfg.lua),
-- then individual env vars A2RUN_* override it.

local R = {}            -- runner state (kept global below so nothing is GC'd)
A2RUNNER = R

local function getenv(k) local v = os.getenv(k); if v == '' then return nil end; return v end

-- ---------- config ----------
local cfg = {
  basic = nil,          -- path to BASIC source to type in, then RUN
  bin = nil,            -- path to raw binary
  load_addr = 0x6000,   -- where to put bin
  call = false,         -- type CALL load_addr (or number = CALL that address)
  boot_frames = 120,    -- frames to wait after start before acting
  run_frames = 300,     -- frames to let the program run before dumping
  line_gap = 2,         -- extra frames between typed BASIC lines
  dumps = {},           -- { {0x300,0x30F}, ... }
  regs = true,
  screen = true,
  snapshot = false,
  wait_peek = nil,      -- { addr=0x300, value=66 } stop early when matched
  max_frames = 3600,    -- hard timeout (60 s emulated)
  out = 'runner_out.txt',
}

local cfgfile = getenv('A2RUN_CFG') or '../Scripts/runner_cfg.lua'
local cfg_err
do
  local f = io.open(cfgfile, 'r')
  if f then
    f:close()
    local ok, t = pcall(dofile, cfgfile)
    if ok and type(t) == 'table' then for k, v in pairs(t) do cfg[k] = v end
    else cfg_err = 'config load failed: ' .. tostring(t) end
  end
end

local function num(s) if not s then return nil end
  s = s:gsub('^%$', '0x'); return tonumber(s) end
local function parse_dumps(s)
  local t = {}
  for a, b in s:gmatch('(%x+)%s*%-%s*(%x+)') do t[#t+1] = { tonumber(a, 16), tonumber(b, 16) } end
  return t
end
cfg.basic       = getenv('A2RUN_BASIC') or cfg.basic
cfg.bin         = getenv('A2RUN_BIN') or cfg.bin
cfg.load_addr   = num(getenv('A2RUN_LOADADDR')) or cfg.load_addr
cfg.boot_frames = num(getenv('A2RUN_BOOTFRAMES')) or cfg.boot_frames
cfg.run_frames  = num(getenv('A2RUN_FRAMES')) or cfg.run_frames
cfg.out         = getenv('A2RUN_OUT') or cfg.out
if getenv('A2RUN_CALL') then cfg.call = (getenv('A2RUN_CALL') == '1') or num(getenv('A2RUN_CALL')) or false end
if getenv('A2RUN_DUMP') then cfg.dumps = parse_dumps(getenv('A2RUN_DUMP')) end
if getenv('A2RUN_SNAPSHOT') then cfg.snapshot = getenv('A2RUN_SNAPSHOT') == '1' end
if getenv('A2RUN_WAITPEEK') then  -- "0300=42"
  local a, v = getenv('A2RUN_WAITPEEK'):match('(%x+)%s*=%s*(%x+)')
  if a then cfg.wait_peek = { addr = tonumber(a, 16), value = tonumber(v, 16) } end
end

-- ---------- output ----------
do local f = io.open(cfg.out, 'w'); if f then f:close() end end
local function log(s)
  local f = io.open(cfg.out, 'a')
  if f then f:write(s .. '\n'); f:close() end
end
local function try(what, fn, ...)
  local ok, err = pcall(fn, ...)
  if not ok then log('ERROR [' .. what .. ']: ' .. tostring(err)) end
  return ok, err
end

log('runner.lua started  ' .. os.date('%Y-%m-%d %H:%M:%S'))
log('config file: ' .. cfgfile .. (cfg_err and ('  (' .. cfg_err .. ')') or ''))
if cfg_err then log('ERROR: ' .. cfg_err) end

-- ---------- helpers ----------
local function cpu() return manager.machine.devices[':maincpu'] end
local function mem() return cpu().spaces['program'] end

local function hexdump(a, b)
  local m = mem()
  log(string.format('--- memory $%04X-$%04X ---', a, b))
  for row = a - (a % 16), b, 16 do
    local hex, asc = {}, {}
    for i = 0, 15 do
      local ad = row + i
      if ad < a or ad > b then hex[#hex+1] = '  '; asc[#asc+1] = ' '
      else
        local v = m:read_u8(ad)
        hex[#hex+1] = string.format('%02X', v)
        local c = v & 0x7F
        asc[#asc+1] = (c >= 0x20 and c < 0x7F) and string.char(c) or '.'
      end
    end
    log(string.format('%04X: %s  %s', row, table.concat(hex, ' '), table.concat(asc)))
  end
end

local function dump_regs()
  local st = cpu().state
  local parts = {}
  for _, r in ipairs({ 'PC', 'A', 'X', 'Y', 'SP', 'P' }) do
    if st[r] then parts[#parts+1] = string.format('%s=%0' .. ((r == 'PC') and 4 or 2) .. 'X', r, st[r].value) end
  end
  log('--- registers ---'); log(table.concat(parts, ' '))
  if st['P'] then
    local p, fl, names = st['P'].value, '', 'NV-BDIZC'
    for i = 7, 0, -1 do fl = fl .. (((p >> i) & 1) == 1 and names:sub(8 - i, 8 - i) or '.') end
    log('flags: ' .. fl)
  end
end

-- 40-column text page 1 ($0400-$07FF), interleaved rows
local function dump_screen()
  local m = mem()
  log('--- text screen (page 1) ---')
  log('+' .. string.rep('-', 40) .. '+')
  for r = 0, 23 do
    local base = 0x400 + (r % 8) * 0x80 + (r // 8) * 0x28
    local t = {}
    for c = 0, 39 do
      local ch = m:read_u8(base + c) & 0x7F
      if ch < 0x20 then ch = ch + 0x40 end     -- inverse/flash letters
      t[#t+1] = string.char(ch)
    end
    log('|' .. table.concat(t) .. '|')
  end
  log('+' .. string.rep('-', 40) .. '+')
end

local function read_file(p, binary)
  local f, e = io.open(p, binary and 'rb' or 'r')
  if not f then error('cannot open ' .. tostring(p) .. ': ' .. tostring(e)) end
  local d = f:read('a'); f:close(); return d
end

-- ---------- typing queue ----------
local queue = {}   -- strings to post, one per entry
local function kb() return manager.machine.natkeyboard end
local function posting()
  local ok, v = pcall(function() return kb().is_posting end)
  return ok and v
end

-- ---------- main state machine ----------
local frame, phase, gap, run_start = 0, 'boot', 0, nil
local finished = false

local function finish(reason)
  if finished then return end
  finished = true
  log('stop reason: ' .. reason .. '  (frame ' .. frame .. ')')
  try('registers', function() if cfg.regs then dump_regs() end end)
  for _, d in ipairs(cfg.dumps or {}) do try('dump', hexdump, d[1], d[2]) end
  try('screen', function() if cfg.screen then dump_screen() end end)
  try('snapshot', function()
    if cfg.snapshot then manager.machine.video:snapshot(); log('snapshot saved (MAME snap folder)') end
  end)
  log('done')
  try('exit', function() manager.machine:exit() end)
end

local function start_actions()
  if cfg.bin then
    try('load bin', function()
      local d = read_file(cfg.bin, true)
      local m = mem()
      for i = 1, #d do m:write_u8(cfg.load_addr + i - 1, d:byte(i)) end
      log(string.format('loaded %s: %d bytes at $%04X-$%04X', cfg.bin, #d, cfg.load_addr, cfg.load_addr + #d - 1))
    end)
    if cfg.call then
      local a = (type(cfg.call) == 'number') and cfg.call or cfg.load_addr
      queue[#queue+1] = 'CALL ' .. a .. '\n'
    end
  end
  if cfg.basic then
    try('read basic', function()
      local src = read_file(cfg.basic, false)
      queue[#queue+1] = 'NEW\n'
      local n = 0
      for line in (src .. '\n'):gmatch('([^\r\n]*)\r?\n') do
        if line:match('%S') then queue[#queue+1] = line .. '\n'; n = n + 1 end
      end
      queue[#queue+1] = 'RUN\n'
      log('BASIC: ' .. n .. ' lines queued from ' .. cfg.basic)
    end)
  end
end

local function tick()
  frame = frame + 1
  if frame >= cfg.max_frames then return finish('max_frames timeout') end
  if phase == 'boot' then
    if frame >= cfg.boot_frames then start_actions(); phase = 'type' end
  elseif phase == 'type' then
    if posting() then return end
    if gap > 0 then gap = gap - 1; return end
    if #queue > 0 then
      kb():post(table.remove(queue, 1)); gap = cfg.line_gap
    else
      phase = 'run'; run_start = frame; log('typing done at frame ' .. frame)
    end
  elseif phase == 'run' then
    if cfg.wait_peek then
      local v = mem():read_u8(cfg.wait_peek.addr)
      if v == cfg.wait_peek.value then
        return finish(string.format('PEEK($%04X)==$%02X', cfg.wait_peek.addr, v))
      end
    end
    if frame - run_start >= cfg.run_frames then finish('run_frames elapsed') end
  end
end

-- MUST be global (stored in A2RUNNER) or the subscription is garbage collected
R.sub = emu.add_machine_frame_notifier(function()
  if finished then return end
  local ok, err = pcall(tick)
  if not ok then log('ERROR [tick]: ' .. tostring(err)); finish('error') end
end)
