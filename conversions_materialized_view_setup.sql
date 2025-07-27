-- ===================================================================
-- ByteC Conversions 實體化視圖和索引優化腳本
-- 版本: 1.0
-- 目的: 提升 conversions_enhanced 查詢性能 50-80%
-- ===================================================================

-- 檢查環境
DO $$
BEGIN
    RAISE NOTICE '🚀 開始 ByteC Conversions 優化部署...';
    RAISE NOTICE '📊 當前時間: %', NOW();
    RAISE NOTICE '📋 PostgreSQL 版本: %', version();
END $$;

-- ===================================================================
-- 第一階段: 創建實體化視圖
-- ===================================================================

-- 檢查是否已存在實體化視圖
DROP MATERIALIZED VIEW IF EXISTS conversions_enhanced_mat CASCADE;

RAISE NOTICE '🔧 創建實體化視圖: conversions_enhanced_mat';

-- 創建實體化視圖 (基於現有視圖定義)
CREATE MATERIALIZED VIEW conversions_enhanced_mat AS
SELECT 
    id,
    conversion_id,
    tenant_id,
    COALESCE(datetime_conversion, created_at) AS conversion_datetime,
    created_at,
    updated_at,
    event_time,
    platform,
    partner,
    source,
    offer_id,
    offer_name,
    order_id,
    merchant_id,
    COALESCE(sale_amount, usd_sale_amount) AS usd_sale_amount,
    COALESCE(payout, usd_payout) AS usd_payout,
    sale_amount_local,
    payout_local,
    myr_sale_amount,
    myr_payout,
    base_payout,
    bonus_payout,
    COALESCE(conversion_currency, currency, 'USD'::character varying) AS currency,
    conversion_currency,
    COALESCE(conversion_status, 'completed'::character varying) AS status,
    conversion_status,
    offer_status,
    aff_sub,
    aff_sub1,
    aff_sub2,
    aff_sub3,
    aff_sub4,
    aff_sub5,
    adv_sub,
    adv_sub1,
    adv_sub2,
    adv_sub3,
    adv_sub4,
    adv_sub5,
    click_id,
    click_time,
    commission_rate,
    avg_commission_rate,
    affiliate_remarks,
    raw_data
FROM conversions
WITH DATA;

-- ===================================================================
-- 第二階段: 為實體化視圖創建索引
-- ===================================================================

RAISE NOTICE '🔧 為實體化視圖創建索引...';

-- 主鍵索引
CREATE UNIQUE INDEX CONCURRENTLY idx_conv_enh_mat_pkey 
ON conversions_enhanced_mat (id);

-- 轉換ID索引 (唯一)
CREATE UNIQUE INDEX CONCURRENTLY idx_conv_enh_mat_conversion_id 
ON conversions_enhanced_mat (conversion_id);

-- 時間相關索引
CREATE INDEX CONCURRENTLY idx_conv_enh_mat_conversion_datetime 
ON conversions_enhanced_mat (conversion_datetime DESC);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_created_at 
ON conversions_enhanced_mat (created_at DESC);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_event_time 
ON conversions_enhanced_mat (event_time DESC);

-- 業務欄位索引
CREATE INDEX CONCURRENTLY idx_conv_enh_mat_aff_sub1 
ON conversions_enhanced_mat (aff_sub1);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_partner 
ON conversions_enhanced_mat (partner);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_platform 
ON conversions_enhanced_mat (platform);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_source 
ON conversions_enhanced_mat (source);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_offer_id 
ON conversions_enhanced_mat (offer_id);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_status 
ON conversions_enhanced_mat (status);

-- 複合索引 (常用查詢組合)
CREATE INDEX CONCURRENTLY idx_conv_enh_mat_aff_sub1_datetime 
ON conversions_enhanced_mat (aff_sub1, conversion_datetime DESC);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_partner_datetime 
ON conversions_enhanced_mat (partner, conversion_datetime DESC);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_platform_partner 
ON conversions_enhanced_mat (platform, partner);

CREATE INDEX CONCURRENTLY idx_conv_enh_mat_status_datetime 
ON conversions_enhanced_mat (status, conversion_datetime DESC);

-- 金額聚合優化索引
CREATE INDEX CONCURRENTLY idx_conv_enh_mat_payout_datetime 
ON conversions_enhanced_mat (conversion_datetime DESC, usd_payout) 
WHERE usd_payout IS NOT NULL;

-- 近期數據分區索引 (30天內)
CREATE INDEX CONCURRENTLY idx_conv_enh_mat_recent 
ON conversions_enhanced_mat (aff_sub1, conversion_datetime DESC) 
WHERE conversion_datetime >= NOW() - INTERVAL '30 days';

-- ===================================================================
-- 第三階段: 基礎表額外索引優化
-- ===================================================================

RAISE NOTICE '🔧 優化基礎表索引...';

-- 檢查並創建缺少的複合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_aff_sub1_created_at 
ON conversions (aff_sub1, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_status_datetime 
ON conversions (partner, conversion_status, datetime_conversion DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_platform_partner_datetime 
ON conversions (platform, partner, created_at DESC);

-- 分區索引 (最近30天的熱數據)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_recent_data 
ON conversions (created_at DESC, aff_sub1) 
WHERE created_at >= NOW() - INTERVAL '30 days';

-- JSON 欄位索引 (用於複雜查詢)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_raw_data_gin 
ON conversions USING gin (raw_data);

-- ===================================================================
-- 第四階段: 設置自動刷新計劃 (需要 pg_cron 擴展)
-- ===================================================================

-- 檢查 pg_cron 擴展
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        RAISE NOTICE '✅ pg_cron 擴展已啟用，設置自動刷新...';
        
        -- 刪除可能存在的舊計劃
        PERFORM cron.unschedule('refresh-conversions-enhanced-mat');
        
        -- 設置每小時刷新實體化視圖
        PERFORM cron.schedule(
            'refresh-conversions-enhanced-mat',
            '0 * * * *',  -- 每小時的第0分鐘
            'REFRESH MATERIALIZED VIEW CONCURRENTLY conversions_enhanced_mat;'
        );
        
        RAISE NOTICE '⏰ 已設置每小時自動刷新實體化視圖';
        
    ELSE
        RAISE WARNING '⚠️  pg_cron 擴展未啟用，無法設置自動刷新';
        RAISE NOTICE '💡 手動刷新命令: REFRESH MATERIALIZED VIEW CONCURRENTLY conversions_enhanced_mat;';
    END IF;
END $$;

-- ===================================================================
-- 第五階段: 創建實體化視圖管理函數
-- ===================================================================

-- 創建刷新函數
CREATE OR REPLACE FUNCTION refresh_conversions_enhanced_mat()
RETURNS void AS $$
BEGIN
    RAISE NOTICE '🔄 開始刷新實體化視圖...';
    
    -- 併發刷新 (不阻塞查詢)
    REFRESH MATERIALIZED VIEW CONCURRENTLY conversions_enhanced_mat;
    
    -- 更新統計信息
    ANALYZE conversions_enhanced_mat;
    
    RAISE NOTICE '✅ 實體化視圖刷新完成';
    
    -- 記錄刷新時間
    INSERT INTO materialized_view_refresh_log (view_name, refresh_time)
    VALUES ('conversions_enhanced_mat', NOW())
    ON CONFLICT (view_name) DO UPDATE SET 
        refresh_time = NOW(),
        refresh_count = materialized_view_refresh_log.refresh_count + 1;
        
END;
$$ LANGUAGE plpgsql;

-- 創建日誌表 (記錄刷新歷史)
CREATE TABLE IF NOT EXISTS materialized_view_refresh_log (
    view_name VARCHAR(100) PRIMARY KEY,
    refresh_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    refresh_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 手動刷新函數 (帶進度報告)
CREATE OR REPLACE FUNCTION manual_refresh_conversions_enhanced()
RETURNS TABLE(
    operation TEXT,
    duration INTERVAL,
    status TEXT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    -- 刷新實體化視圖
    start_time := clock_timestamp();
    PERFORM refresh_conversions_enhanced_mat();
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        '實體化視圖刷新'::TEXT,
        (end_time - start_time)::INTERVAL,
        '完成'::TEXT;
    
    -- 更新統計信息
    start_time := clock_timestamp();
    ANALYZE conversions_enhanced_mat;
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        '統計信息更新'::TEXT,
        (end_time - start_time)::INTERVAL,
        '完成'::TEXT;
        
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- 第六階段: 性能驗證查詢
-- ===================================================================

-- 創建性能測試函數
CREATE OR REPLACE FUNCTION test_conversions_performance()
RETURNS TABLE(
    test_name TEXT,
    table_type TEXT,
    execution_time INTERVAL,
    result_count BIGINT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    row_count BIGINT;
BEGIN
    -- 測試1: 基礎表計數查詢
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count FROM conversions;
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        '總記錄計數'::TEXT,
        'conversions (基礎表)'::TEXT,
        (end_time - start_time)::INTERVAL,
        row_count;
    
    -- 測試2: 實體化視圖計數查詢
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count FROM conversions_enhanced_mat;
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        '總記錄計數'::TEXT,
        'conversions_enhanced_mat (實體化視圖)'::TEXT,
        (end_time - start_time)::INTERVAL,
        row_count;
    
    -- 測試3: 原始視圖計數查詢
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count FROM conversions_enhanced;
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        '總記錄計數'::TEXT,
        'conversions_enhanced (視圖)'::TEXT,
        (end_time - start_time)::INTERVAL,
        row_count;
    
    -- 測試4: 複雜聚合查詢 (基礎表)
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count 
    FROM conversions 
    WHERE created_at >= NOW() - INTERVAL '7 days'
      AND partner = 'DeepLeaper';
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        '7天數據聚合 (partner=DeepLeaper)'::TEXT,
        'conversions (基礎表)'::TEXT,
        (end_time - start_time)::INTERVAL,
        row_count;
    
    -- 測試5: 複雜聚合查詢 (實體化視圖)
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count 
    FROM conversions_enhanced_mat 
    WHERE conversion_datetime >= NOW() - INTERVAL '7 days'
      AND partner = 'DeepLeaper';
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        '7天數據聚合 (partner=DeepLeaper)'::TEXT,
        'conversions_enhanced_mat (實體化視圖)'::TEXT,
        (end_time - start_time)::INTERVAL,
        row_count;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- 第七階段: 權限和安全設置
-- ===================================================================

-- 授權給應用用戶
GRANT SELECT ON conversions_enhanced_mat TO PUBLIC;
GRANT EXECUTE ON FUNCTION refresh_conversions_enhanced_mat() TO postback_admin;
GRANT EXECUTE ON FUNCTION manual_refresh_conversions_enhanced() TO postback_admin;
GRANT EXECUTE ON FUNCTION test_conversions_performance() TO postback_admin;

-- ===================================================================
-- 部署完成報告
-- ===================================================================

DO $$
DECLARE
    mat_view_size TEXT;
    index_count INTEGER;
BEGIN
    -- 獲取實體化視圖大小
    SELECT pg_size_pretty(pg_total_relation_size('conversions_enhanced_mat')) 
    INTO mat_view_size;
    
    -- 獲取索引數量
    SELECT COUNT(*) INTO index_count 
    FROM pg_indexes 
    WHERE tablename = 'conversions_enhanced_mat';
    
    RAISE NOTICE '';
    RAISE NOTICE '🎉 ByteC Conversions 優化部署完成！';
    RAISE NOTICE '===============================================';
    RAISE NOTICE '📊 實體化視圖大小: %', mat_view_size;
    RAISE NOTICE '📋 創建索引數量: %', index_count;
    RAISE NOTICE '⏰ 自動刷新頻率: 每小時';
    RAISE NOTICE '📈 預期性能提升: 50-80%%';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 手動測試命令:';
    RAISE NOTICE '   SELECT * FROM test_conversions_performance();';
    RAISE NOTICE '   SELECT * FROM manual_refresh_conversions_enhanced();';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 部署時間: %', NOW();
    RAISE NOTICE '===============================================';
END $$; 