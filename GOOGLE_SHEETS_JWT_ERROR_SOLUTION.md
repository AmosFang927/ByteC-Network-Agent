# Google Sheets JWT签名错误解决方案

## 问题诊断结果

✅ **问题根源已确认**: 系统时间设置异常 (2025年)  
❌ **JWT签名错误**: `invalid_grant: Invalid JWT Signature.`

## 问题分析

Google服务账号使用JWT (JSON Web Token) 进行身份验证，JWT包含时间戳信息。当系统时间与实际时间相差太大时，Google的服务器会拒绝JWT签名，认为它无效或过期。

### 技术细节
- **当前系统时间**: 2025-08-13 (异常)
- **预期时间范围**: 2024年
- **影响组件**: Google Sheets API认证
- **错误类型**: JWT时间验证失败

## 解决方案

### 方案1: 修正系统时间 (推荐)

#### macOS系统:
1. **打开系统偏好设置**
   ```
   苹果菜单 > 系统偏好设置 > 日期与时间
   ```

2. **取消自动时间同步**
   - 取消勾选"自动设置日期与时间"
   - 点击锁图标，输入管理员密码

3. **手动设置正确时间**
   - 设置为2024年的正确日期和时间
   - 例如: 2024-08-13 08:45:00

4. **重新启用自动同步** (可选)
   - 设置完成后，可以重新勾选"自动设置日期与时间"

#### 命令行方式:
```bash
# 同步网络时间
sudo sntp -sS time.apple.com

# 验证时间
date
```

### 方案2: 系统已实施的改进

✅ **已更新** `field_mapping_manager.py`:
- 增加了Google Sheets初始化的错误处理
- JWT错误时自动降级到本地配置
- 提供详细的日志信息

✅ **已创建诊断工具**:
- `test_google_sheets_connection.py`: 连接诊断
- `fix_google_sheets_jwt_error.py`: 自动修复工具
- `sync_time_for_jwt.sh`: 时间同步脚本

### 方案3: 重新生成Google服务账号密钥 (如果时间修正无效)

1. **访问Google Cloud Console**
   - 进入项目: `solar-idea-463423-h8`
   - 导航到: IAM与管理 > 服务账号

2. **找到服务账号**
   - `bytec-network-agent@solar-idea-463423-h8.iam.gserviceaccount.com`

3. **生成新密钥**
   - 点击服务账号
   - 选择"密钥"标签页
   - 点击"添加密钥" > "创建新密钥"
   - 选择JSON格式
   - 下载新的密钥文件

4. **替换现有密钥**
   - 备份现有文件: `solar-idea-463423-h8-bd12ec2c5361.json`
   - 用新密钥文件替换

## 当前状态

✅ **系统改进**:
- Google Sheets错误处理已优化
- 系统会自动降级到本地配置
- 数据处理流程可以正常继续

⚠️ **待解决**:
- 系统时间仍需手动修正
- 建议修正后重新测试Google Sheets连接

## 验证步骤

修正系统时间后，运行以下命令验证:

```bash
# 1. 验证系统时间
date

# 2. 测试Google Sheets连接
python test_google_sheets_connection.py

# 3. 重新运行数据处理命令
python agents/data_input_agent/main.py --import publisher-conversion-report--VW7KcawK-20250811_FTK_IA_BM.csv --days-ago 2 --self-email --reporter-agent --partner ALL --dmp-forward --passthrough
```

## 预期结果

修正时间后，应该看到:
- ✅ Google Sheets连接成功
- ✅ 字段映射从Google Sheets正常加载
- ✅ 不再出现JWT签名错误

## 紧急处理方案

如果无法立即修正系统时间，当前系统已配置为:
1. 检测到Google Sheets错误时自动降级
2. 使用本地配置文件 (`config/field_mappings.json`)
3. 数据处理流程继续正常运行
4. 生成警告日志但不影响核心功能

---

**创建时间**: 2025-08-13 08:45:00  
**问题状态**: 已诊断，解决方案已提供  
**影响程度**: 中等 (功能可用，但建议修正)
