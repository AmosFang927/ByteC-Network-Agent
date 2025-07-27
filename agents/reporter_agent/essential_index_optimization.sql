-- ===================================================================
-- ByteC Reporter-Agent 關鍵索引優化腳本
-- 版本: 2.0 (極簡優化版本)
-- 目的: 針對 reporter-agent 查詢模式的關鍵索引，預期性能提升 70-80%
-- ===================================================================

-- 檢查環境
DO $$
BEGIN
    RAISE NOTICE '🚀 開始 Reporter-Agent 關鍵索引優化...';
    RAISE NOTICE '📊 當前時間: %', NOW();
    RAISE NOTICE '🎯 目標: 支援極簡查詢邏輯的高效索引';
END $$;

-- ===================================================================
-- 第一階段: 分析當前索引狀況
-- ===================================================================

DO $$
DECLARE
    index_info RECORD;
    index_count INTEGER;
    table_size TEXT;
BEGIN
    RAISE NOTICE '📋 分析 conversions 表現狀...';
    
    -- 獲取表大小
    SELECT pg_size_pretty(pg_total_relation_size('conversions')) INTO table_size;
    RAISE NOTICE '📊 表格大小: %', table_size;
    
    -- 獲取記錄數量
    SELECT COUNT(*) INTO index_count FROM conversions;
    RAISE NOTICE '📊 記錄數量: %', index_count;
    
    -- 列出現有索引
    SELECT COUNT(*) INTO index_count FROM pg_indexes WHERE tablename = 'conversions';
    RAISE NOTICE '🔍 現有索引數量: %', index_count;
    
    FOR index_info IN 
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'conversions'
        ORDER BY indexname
    LOOP
        RAISE NOTICE '  - %', index_info.indexname;
    END LOOP;
END $$;

-- ===================================================================
-- 第二階段: 創建 Reporter-Agent 關鍵索引
-- ===================================================================

RAISE NOTICE '🔧 創建 Reporter-Agent 關鍵索引...';

-- 1. ID 字段索引 (支持優化游標分頁)
-- 這是最重要的索引，用於 id < last_id 的高效分頁
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_conversions_id_desc_reporter') THEN
        CREATE INDEX CONCURRENTLY idx_conversions_id_desc_reporter 
        ON conversions (id DESC);
        RAISE NOTICE '✅ 創建 ID 降序索引 (游標分頁優化)';
    ELSE
        RAISE NOTICE '⚠️ ID 索引已存在';
    END IF;
END $$;

-- 2. datetime_conversion 索引 (時間範圍查詢)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_conversions_datetime_reporter') THEN
        CREATE INDEX CONCURRENTLY idx_conversions_datetime_reporter 
        ON conversions (datetime_conversion DESC) 
        WHERE datetime_conversion IS NOT NULL;
        RAISE NOTICE '✅ 創建 datetime_conversion 索引';
    ELSE
        RAISE NOTICE '⚠️ datetime_conversion 索引已存在';
    END IF;
END $$;

-- 3. partner 字段索引 (Partner 過濾)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_conversions_partner_reporter') THEN
        CREATE INDEX CONCURRENTLY idx_conversions_partner_reporter 
        ON conversions (partner) 
        WHERE partner IS NOT NULL;
        RAISE NOTICE '✅ 創建 partner 索引';
    ELSE
        RAISE NOTICE '⚠️ partner 索引已存在';
    END IF;
END $$;

-- 4. 複合索引: partner + datetime_conversion (常用查詢組合)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_conversions_partner_datetime_reporter') THEN
        CREATE INDEX CONCURRENTLY idx_conversions_partner_datetime_reporter 
        ON conversions (partner, datetime_conversion DESC) 
        WHERE partner IS NOT NULL AND datetime_conversion IS NOT NULL;
        RAISE NOTICE '✅ 創建 partner + datetime_conversion 複合索引';
    ELSE
        RAISE NOTICE '⚠️ partner + datetime_conversion 索引已存在';
    END IF;
END $$;

-- 5. 複合索引: datetime_conversion + id (支持時間範圍 + 游標分頁)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_conversions_datetime_id_reporter') THEN
        CREATE INDEX CONCURRENTLY idx_conversions_datetime_id_reporter 
        ON conversions (datetime_conversion DESC, id DESC) 
        WHERE datetime_conversion IS NOT NULL;
        RAISE NOTICE '✅ 創建 datetime_conversion + id 複合索引';
    ELSE
        RAISE NOTICE '⚠️ datetime_conversion + id 索引已存在';
    END IF;
END $$;

-- 6. 複合索引: partner + id (支持 Partner 過濾 + 游標分頁)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_conversions_partner_id_reporter') THEN
        CREATE INDEX CONCURRENTLY idx_conversions_partner_id_reporter 
        ON conversions (partner, id DESC) 
        WHERE partner IS NOT NULL;
        RAISE NOTICE '✅ 創建 partner + id 複合索引';
    ELSE
        RAISE NOTICE '⚠️ partner + id 索引已存在';
    END IF;
END $$;

-- ===================================================================
-- 第三階段: 驗證索引創建結果
-- ===================================================================

DO $$
DECLARE
    index_info RECORD;
    new_index_count INTEGER;
BEGIN
    RAISE NOTICE '🔍 驗證索引創建結果...';
    
    SELECT COUNT(*) INTO new_index_count 
    FROM pg_indexes 
    WHERE tablename = 'conversions' 
    AND indexname LIKE '%_reporter';
    
    RAISE NOTICE '📊 Reporter-Agent 專用索引數量: %', new_index_count;
    
    FOR index_info IN 
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'conversions' 
        AND indexname LIKE '%_reporter'
        ORDER BY indexname
    LOOP
        RAISE NOTICE '  ✅ %', index_info.indexname;
    END LOOP;
END $$;

-- ===================================================================
-- 第四階段: 查詢優化建議
-- ===================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎯 查詢優化建議:';
    RAISE NOTICE '  1. 使用 ORDER BY id DESC 進行游標分頁';
    RAISE NOTICE '  2. WHERE 條件優先使用 partner 和 datetime_conversion';
    RAISE NOTICE '  3. 避免 ORDER BY datetime_conversion，改用 ORDER BY id DESC';
    RAISE NOTICE '  4. 批次大小建議 5000 條記錄';
    RAISE NOTICE '  5. 使用 id < last_id 代替 OFFSET 分頁';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Reporter-Agent 關鍵索引優化完成!';
    RAISE NOTICE '📈 預期性能提升: 70-80%';
END $$; 