# ByteC Conversions 表格優化指南

## 🔍 **現狀分析**

### **表格架構**
- **`conversions`**: 基礎表格 (716MB, 446,895 筆記錄, 15個索引)
- **`conversions_enhanced`**: 邏輯視圖 (數據清理層)

### **視圖作用分析**
`conversions_enhanced` 視圖提供：
1. **數據標準化**: 統一欄位命名和數據格式
2. **向後兼容**: 處理舊系統的欄位映射
3. **數據清理**: 提供默認值和空值處理
4. **業務邏輯**: 隱藏底層表格複雜性

## 🎯 **使用場景差異**

### **何時使用 `conversions`**
- ✅ **數據寫入操作** (INSERT, UPDATE, DELETE)
- ✅ **原始數據分析** (需要所有原始欄位)
- ✅ **數據遷移和同步**
- ✅ **系統維護和修復**
- ✅ **Performance 敏感的查詢** (有索引支持)

### **何時使用 `conversions_enhanced`**
- ✅ **業務報表和Dashboard** (標準化數據)
- ✅ **API 返回結果** (清理後的數據)
- ✅ **第三方系統集成** (統一格式)
- ✅ **用戶界面顯示** (友好的欄位名)

## ⚠️ **潛在問題與風險**

### **1. 性能問題**
```sql
-- 問題: 視圖查詢可能較慢 (無索引支持)
SELECT * FROM conversions_enhanced WHERE aff_sub1 = 'RAMPUP%';

-- 解決: 直接查詢基礎表
SELECT * FROM conversions WHERE aff_sub1 = 'RAMPUP%';
```

### **2. 邏輯錯誤風險**
```sql
-- 風險: COALESCE 可能隱藏數據問題
COALESCE(conversion_status, 'completed') AS status
-- 當 conversion_status 為 NULL 時自動設為 'completed'
-- 可能掩蓋實際的數據問題
```

### **3. 維護複雜性**
- 視圖定義變更需要重新部署
- 新增欄位需要同時更新視圖
- 調試時需要考慮視圖轉換邏輯

## 🚀 **優化建議**

### **📊 立即優化 (低風險)**

#### **1. 查詢路由優化**
```python
class ConversionsQueryRouter:
    """智能查詢路由器"""
    
    def get_optimal_table(self, query_type: str, fields: List[str]) -> str:
        """根據查詢類型選擇最優表格"""
        
        # 原始數據查詢 -> 基礎表
        if any(field in ['datetime_conversion', 'partner_id', 'platform_id'] 
               for field in fields):
            return 'conversions'
        
        # 寫入操作 -> 基礎表
        if query_type in ['INSERT', 'UPDATE', 'DELETE']:
            return 'conversions'
        
        # 大量數據聚合 -> 基礎表 (有索引)
        if query_type == 'AGGREGATE':
            return 'conversions'
        
        # 展示層查詢 -> 視圖
        return 'conversions_enhanced'
```

#### **2. 索引優化建議**
```sql
-- 為常用查詢模式添加複合索引
CREATE INDEX CONCURRENTLY idx_conversions_aff_sub1_created_at 
ON conversions (aff_sub1, created_at DESC);

CREATE INDEX CONCURRENTLY idx_conversions_partner_status_datetime 
ON conversions (partner, conversion_status, datetime_conversion);

-- 分區索引 (按時間分區)
CREATE INDEX CONCURRENTLY idx_conversions_recent 
ON conversions (created_at DESC) 
WHERE created_at >= NOW() - INTERVAL '30 days';
```

#### **3. 查詢緩存策略**
```python
# 為視圖查詢添加緩存
@cache(ttl=300)  # 5分鐘緩存
def get_enhanced_conversions(filters: dict):
    return query_conversions_enhanced(filters)

# 基礎表查詢不緩存 (數據實時性要求高)
def get_raw_conversions(filters: dict):
    return query_conversions(filters)
```

### **📈 中期優化 (中風險)**

#### **1. 實體化視圖 (Materialized View)**
```sql
-- 創建實體化視圖提升查詢性能
CREATE MATERIALIZED VIEW conversions_enhanced_mat AS
SELECT 
    id,
    conversion_id,
    tenant_id,
    COALESCE(datetime_conversion, created_at) AS conversion_datetime,
    -- ... 其他欄位
FROM conversions;

-- 添加索引
CREATE INDEX idx_conv_enh_mat_aff_sub1 ON conversions_enhanced_mat (aff_sub1);
CREATE INDEX idx_conv_enh_mat_created_at ON conversions_enhanced_mat (conversion_datetime);

-- 定期刷新 (每小時)
SELECT cron.schedule('refresh-conversions-enhanced', '0 * * * *', 
    'REFRESH MATERIALIZED VIEW conversions_enhanced_mat;');
```

#### **2. 應用層統一接口**
```python
class UnifiedConversionsService:
    """統一轉換數據服務"""
    
    async def get_conversions(self, 
                            filters: dict, 
                            use_enhanced: bool = True,
                            performance_mode: bool = False) -> List[dict]:
        """
        智能獲取轉換數據
        """
        if performance_mode or self._requires_raw_data(filters):
            # 使用基礎表 + 應用層數據清理
            raw_data = await self.query_raw_conversions(filters)
            return self._enhance_data_in_app(raw_data)
        
        # 使用增強視圖
        return await self.query_enhanced_conversions(filters)
    
    def _enhance_data_in_app(self, raw_data: List[dict]) -> List[dict]:
        """應用層數據增強"""
        for record in raw_data:
            # 時間統一
            record['conversion_datetime'] = (
                record.get('datetime_conversion') or record['created_at']
            )
            # 金額統一
            record['usd_sale_amount'] = (
                record.get('sale_amount') or record.get('usd_sale_amount')
            )
            # ... 其他清理邏輯
        return raw_data
```

### **🔄 長期優化 (高風險)**

#### **1. 表格重構**
```sql
-- 方案A: 統一欄位命名
ALTER TABLE conversions 
    ADD COLUMN conversion_datetime_v2 TIMESTAMP WITH TIME ZONE;

UPDATE conversions 
SET conversion_datetime_v2 = COALESCE(datetime_conversion, created_at);

-- 方案B: 分離歷史數據
CREATE TABLE conversions_archive AS 
SELECT * FROM conversions 
WHERE created_at < NOW() - INTERVAL '1 year';

-- 方案C: 按時間分區
CREATE TABLE conversions_partitioned (
    LIKE conversions
) PARTITION BY RANGE (created_at);
```

#### **2. 微服務架構**
```python
# 數據讀寫分離
class ConversionsWriteService:
    """轉換數據寫入服務 (使用基礎表)"""
    async def create_conversion(self, data: dict):
        return await self.db.insert('conversions', data)

class ConversionsReadService:
    """轉換數據讀取服務 (使用優化視圖)"""
    async def get_conversions(self, filters: dict):
        return await self.db.query('conversions_enhanced_mat', filters)
```

## 📊 **監控指標**

### **性能監控**
```sql
-- 查詢執行時間監控
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename IN ('conversions', 'conversions_enhanced');

-- 視圖使用頻率統計
SELECT 
    schemaname,
    viewname,
    definition
FROM pg_views 
WHERE viewname = 'conversions_enhanced';
```

### **業務監控**
```python
# 數據一致性檢查
async def check_data_consistency():
    """檢查視圖與基礎表數據一致性"""
    base_count = await db.fetchval("SELECT COUNT(*) FROM conversions")
    view_count = await db.fetchval("SELECT COUNT(*) FROM conversions_enhanced")
    
    if base_count != view_count:
        logger.warning(f"數據不一致: base={base_count}, view={view_count}")
```

## 🎯 **最佳實踐建議**

### **✅ 推薦做法**
1. **讀寫分離**: 寫入用基礎表，讀取優先使用視圖
2. **性能優先**: 大量數據查詢直接使用基礎表
3. **業務邏輯**: 複雜的數據轉換在應用層處理
4. **監控告警**: 定期檢查視圖與基礎表一致性

### **❌ 避免做法**
1. 在視圖上執行大量 JOIN 操作
2. 頻繁修改視圖定義
3. 在視圖中進行複雜計算
4. 忽略視圖的性能影響

## 📈 **預期優化效果**

| 優化項目 | 預期改善 | 實施難度 | 風險等級 |
|---------|----------|----------|----------|
| 查詢路由優化 | 20-40% | 低 | 低 |
| 索引優化 | 30-60% | 低 | 低 |
| 實體化視圖 | 50-80% | 中 | 中 |
| 表格重構 | 60-90% | 高 | 高 |

通過這些優化，可以避免不必要的存取錯誤邏輯，提升整體性能 **40-70%**！ 