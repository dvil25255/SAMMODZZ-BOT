-- ============================================================================
-- ULTIMATE BYPASS & UI SPOOFING SYSTEM (For SAMMODZZ BOT)
-- ============================================================================

local function startBaselineHacks()
    local GameplayData = require("GameLua.GameCore.Data.GameplayData")
    local EPawnState = import("EPawnState")
    local UKismetSystemLibrary = import("KismetSystemLibrary")
    
    _G.g_masterahsanyt = _G.g_masterahsanyt or "@MasterAhsanYT"
    
    -- ========================================================================
    -- ULTIMATE WALLHACK + ESP DETECTION BYPASS
    -- ========================================================================
    local function _BYPASS_InstallUltimateWallhackBypass()
        if _G.__ULTIMATE_WH_BYPASS_LOADED then return end
        local nop = function() end
        local function isBypassActive() return _G._WHA_BYPASS_ACTIVE == true end

        ---------- LAYER 1: PrimitiveSceneProxy override ----------
        pcall(function()
            local FPSP = import("PrimitiveSceneProxy")
            if FPSP then
                local origGetViewRelevance = FPSP.GetViewRelevance
                FPSP.GetViewRelevance = function(self, View)
                    local VR = origGetViewRelevance(self, View)
                    if isBypassActive() and VR then
                        VR.bRenderCustomDepth = false
                        VR.bUsesSceneDepth = false
                    end
                    return VR
                end
                local origDepthPriority = FPSP.GetDepthPriorityGroup
                FPSP.GetDepthPriorityGroup = function(self)
                    if not isBypassActive() then return origDepthPriority(self) end
                    return 0
                end
            end
        end)

        ---------- LAYER 4: RHI depth state interception ----------
        pcall(function()
            local FRHI = import("RHICommandList")
            if FRHI and FRHI.SetDepthState then
                local origSetDepth = FRHI.SetDepthState
                FRHI.SetDepthState = function(self, State)
                    if isBypassActive() and type(State) == "table" and State.DepthEnable ~= nil then
                        State.DepthEnable = true
                    end
                    return origSetDepth(self, State)
                end
            end
        end)

        ---------- LAYER 6: Material property queries ----------
        pcall(function()
            local UMat = import("Material")
            local UMatInst = import("MaterialInstance")
            local UMatDyn = import("MaterialInstanceDynamic")
            if UMat then
                UMat.__origDDT = UMat.GetDisableDepthTest
                UMat.GetDisableDepthTest = function(self) if not isBypassActive() then return UMat.__origDDT(self) end return false end
                UMat.__origHash = UMat.GetMaterialHash
                UMat.GetMaterialHash = function(self) if not isBypassActive() then return UMat.__origHash(self) end return "FAKE_HASH" end
                UMat.__origVM = UMat.VerifyMaterial
                UMat.VerifyMaterial = function(self) if not isBypassActive() then return UMat.__origVM(self) end return true end
            end
            if UMatDyn then
                local oldGetVec = UMatDyn.K2_GetVectorParameterValue
                UMatDyn.K2_GetVectorParameterValue = function(self, name)
                    if not isBypassActive() then return oldGetVec(self, name) end
                    local n = tostring(name or "")
                    if n:find("Color") or n:find("Emissive") or n:find("Tint") then return {R=255,G=255,B=255,A=255} end
                    return oldGetVec(self, name)
                end
            end
        end)

        ---------- LAYER 8: Kernel & memory spoof ----------
        pcall(function()
            local SubMgr = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
            if SubMgr then
                local kc = SubMgr:Get("ClientKernelCheckSubsystem")
                if kc and not kc.__akhooked then
                    local origIKC = kc.IsKernelClean
                    kc.IsKernelClean = function(self) if not isBypassActive() then return origIKC(self) end return true, { code = 0, message = "clean" } end
                    kc.__akhooked = true
                end
            end
        end)

        _G.__ULTIMATE_WH_BYPASS_LOADED = true
        print("[ok] Ultimate Wallhack + ESP Detection Bypass Installed")
    end

    -- ========================================================================
    -- UI SPOOFING & DETECTION SUBSYSTEM SPOOF
    -- ========================================================================
    local function _BYPASS_SetupWHABypassTable()
        local bypass = {}
        local function nop() end
        local function returnTrue() return true end
        local function returnFalse() return false end
        local function safe_require(mod) local ok, res = pcall(require, mod) return ok and res or nil end
        local function tryImport(name) local ok, lib = pcall(import, name) return ok and lib or nil end

        local function blockScreenshots()
            pcall(function()
                local SS = tryImport("ScreenshotMaker") or tryImport("ScreenshotMTDer")
                if SS then
                    SS.MakePicture = function() return "" end
                    SS.ReMakePicture = function() return "" end
                    SS.HasCaptured = returnTrue
                end
            end)
        end

        local function blockGameplayCallbacks()
            if not _G.GameplayCallbacks then _G.GameplayCallbacks = {} end
            local GC = _G.GameplayCallbacks
            local reportFuncs = {
                "ReportAttackFlow","ReportSecAttackFlow","ReportHurtFlow","ReportFireArms",
                "ReportVerifyInfoFlow","ReportMrpcsFlow","ReportPlayerBehavior","ReportTeammatHurt",
                "ReportPlayerMoveRoute","ReportPlayerPosition","ReportAimFlow","ReportHitFlow",
                "ReportWallHack","ReportAimbot","ReportSpeedHack","ReportMagicBullet",
                "ReportAbnormalMaterial","ReportDepthTestChange","ReportMemoryException",
                "ReportMaterialScan","ReportShaderOverride"
            }
            for _, fn in ipairs(reportFuncs) do GC[fn] = nop end

            local oldStateChanged = GC.OnDSPlayerStateChanged
            GC.OnDSPlayerStateChanged = function(UID, state, ...)
                if state and type(state) == "string" then
                    local s = state:lower()
                    if s:find("cheat") or s:find("ban") or s:find("integrity") then return end
                end
                if oldStateChanged then return oldStateChanged(UID, state, ...) end
            end
        end

        local function spoofTssSdk()
            pcall(function()
                local t = _G.TssSdk
                if t then
                    t.GetFileMD5 = function() return "" end
                    t.VerifyFileSignature = returnTrue
                    t.CheckIntegrity = returnTrue
                    t.ScanMemory = function() return true, {} end
                    t.IsEmulator = returnFalse
                    t.OnRecvData = nop
                end
            end)
        end

        local function disableDetectionSubsystems()
            local sm = safe_require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
            if not sm then return end
            local targetSubs = {
                "ClientWallhackDetectionSubsystem", "ClientESPDetectionSubsystem",
                "ClientAimTrackingSubsystem", "ShootVerifySubSystemClient",
                "ClientRenderCheckSubsystem", "ClientMemoryGuardSubsystem",
                "ClientKernelCheckSubsystem", "ClientHawkEyePatrolSubsystem",
                "ClientAntiCheatSubsystem", "IntegrityCheckSubsystem", "FileCheckSubsystem"
            }
            for _, sn in ipairs(targetSubs) do
                local sub = sm:Get(sn)
                if sub and type(sub) == "table" then
                    for k, v in pairs(sub) do
                        if type(v) == "function" then
                            if k:find("Report") or k:find("Send") or k:find("Verify") or
                               k:find("Check") or k:find("Detect") or k:find("Scan") then
                                sub[k] = nop
                            end
                        end
                    end
                end
            end
        end

        function bypass.Init()
            blockScreenshots()
            blockGameplayCallbacks()
            spoofTssSdk()
            disableDetectionSubsystems()
        end

        _G.WHABypass = bypass
    end

    -- ========================================================================
    -- BYPASS EXECUTION
    -- ========================================================================
    local function _BYPASS_Execute()
        if _G._BYPASS_DONE then return end
        local ok, err = pcall(function()
            _G._WHA_BYPASS_ACTIVE = true
            _BYPASS_InstallUltimateWallhackBypass()
            _BYPASS_SetupWHABypassTable()
            if _G.WHABypass and _G.WHABypass.Init then
                _G.WHABypass.Init()
            end
            _G._BYPASS_DONE = true
            print("[ORDER] All bypasses executed")
        end)
        if not ok then
            print("[ORDER] Bypass failed, will retry:", tostring(err))
            _G._BYPASS_DONE = false
        end
    end

    _G._BYPASS_Execute = _BYPASS_Execute
end

startBaselineHacks()
