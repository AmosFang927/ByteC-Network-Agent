-- ============================================
-- ByteC Network Agent 數據庫索引優化腳本
-- 目的：優化 reporter-agent 查詢性能
-- ============================================

-- 創建日期和檢查現有索引
SELECT 
    current_timestamp as optimization_start_time,
    'ByteC Network Database Index Optimization' as script_name;

-- 檢查現有索引
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'conversions'
ORDER BY tablename, indexname;

-- ============================================
-- 主要性能優化索引
-- ============================================

-- 1. 主要查詢索引：日期範圍查詢
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime 
ON conversions (datetime_conversion);

-- 2. Partner查詢索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner 
ON conversions (partner);

-- 3. 複合索引：日期 + Partner（最常用查詢組合）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime_partner 
ON conversions (DATE(datetime_conversion), partner);

-- 4. 複合索引：Partner + 日期降序（用於最新記錄查詢）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_datetime 
ON conversions (partner, datetime_conversion DESC);

-- 5. 日期降序索引（用於 ORDER BY datetime_conversion DESC）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime_desc 
ON conversions (datetime_conversion DESC);

-- ============================================
-- 映射關係優化索引
-- ============================================

-- 6. AFF_SUB索引（用於source映射）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_aff_sub 
ON conversions (aff_sub);

-- 7. Platform ID索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_platform_id 
ON conversions (platform_id);

-- 8. Partner ID索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_id 
ON conversions (partner_id);

-- ============================================
-- 進階優化索引
-- ============================================

-- 9. 複合索引：日期 + 狀態（用於狀態過濾）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime_status 
ON conversions (datetime_conversion, conversion_status);

-- 10. 複合索引：Partner + AFF_SUB（用於詳細報表查詢）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_aff_sub 
ON conversions (partner, aff_sub);

-- 11. Tenant ID索引（多租戶查詢）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_tenant_id 
ON conversions (tenant_id);

-- 12. Created_at索引（用於按創建時間查詢）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_created_at 
ON conversions (created_at);

-- ============================================
-- 部分索引（針對特定條件優化）
-- ============================================

-- 13. 非空Partner索引（跳過空值）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_not_null 
ON conversions (partner) 
WHERE partner IS NOT NULL AND partner != '';

-- 14. 非空AFF_SUB索引（跳過空值）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_aff_sub_not_null 
ON conversions (aff_sub) 
WHERE aff_sub IS NOT NULL AND aff_sub != '';

-- 15. 最近30天數據索引（熱數據優化）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_recent_30days 
ON conversions (datetime_conversion, partner) 
WHERE datetime_conversion >= CURRENT_DATE - INTERVAL '30 days';

-- ============================================
-- 函數索引（針對特定查詢模式）
-- ============================================

-- 16. 日期函數索引（DATE(datetime_conversion)）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_date_only 
ON conversions (DATE(datetime_conversion));

-- 17. 大寫Partner索引（避免大小寫敏感問題）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_upper 
ON conversions (UPPER(partner));

-- ============================================
-- 統計信息更新
-- ============================================

-- 更新表統計信息以優化查詢計劃
ANALYZE conversions;

-- ============================================
-- 索引使用情況檢查
-- ============================================

-- 檢查新創建的索引
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'conversions'
    AND indexname LIKE 'idx_conversions_%'
ORDER BY indexname;

-- 檢查表大小和索引大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE tablename = 'conversions';

-- ============================================
-- 性能建議
-- ============================================

/*
索引優化完成後的性能提升預期：

1. 日期範圍查詢：提升 80-90%
2. Partner查詢：提升 70-85%
3. 複合查詢（日期+Partner）：提升 85-95%
4. ORDER BY datetime_conversion DESC：提升 90-95%
5. 映射查詢（aff_sub, partner_id）：提升 60-80%

注意事項：
- 索引會增加寫入成本（INSERT/UPDATE）約 5-10%
- 索引會佔用額外存儲空間（約為表大小的 20-40%）
- 定期執行 ANALYZE 以保持統計信息準確性
- 監控索引使用情況，移除未使用的索引

監控查詢：
SELECT * FROM pg_stat_user_indexes WHERE relname = 'conversions';
*/

-- 完成時間記錄
SELECT 
    current_timestamp as optimization_end_time,
    'Index optimization completed successfully' as status; 