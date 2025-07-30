# TikTok Shop 联盟营销 - main.py 使用指南

## 📋 **完整参数说明**

```bash
python agents/linkshare_agent/main.py [OPTIONS]
```

### **可用参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--product-id` | string | `1731493745807886173` | TikTok Shop 产品ID |
| `--tags` | list | `L_OEM1_XIAOMI_PUSH_ID L_OEM3_OPPO_PUSH_ID L_OEM2_VIVO_PUSH_ID` | 联盟标签列表 |
| `--refresh-token` | flag | false | 主动调用refresh token API更新token |
| `--help` | flag | - | 显示帮助信息 |

## 🚀 **使用示例**

### **示例1: 使用默认参数生成链接**
```bash
python agents/linkshare_agent/main.py
```
- 使用默认产品ID: `1731493745807886173`
- 使用默认标签: `L_OEM1_XIAOMI_PUSH_ID`, `L_OEM3_OPPO_PUSH_ID`, `L_OEM2_VIVO_PUSH_ID`
- 使用现有token (如果有效)

### **示例2: 指定产品ID**
```bash
python agents/linkshare_agent/main.py --product-id 1234567890123456789
```
- 使用指定的产品ID
- 使用默认标签
- 使用现有token

### **示例3: 指定产品ID和自定义标签**
```bash
python agents/linkshare_agent/main.py \
  --product-id 1731493745807886173 \
  --tags L_OEM1_XIAOMI_PUSH_ID L_OEM3_OPPO_PUSH_ID L_OEM2_VIVO_PUSH_ID
```
- 使用指定的产品ID
- 使用自定义标签列表
- 使用现有token

### **示例4: 主动刷新Token**
```bash
python agents/linkshare_agent/main.py --refresh-token
```
- 主动调用refresh token API
- 获取新的access token和refresh token
- 使用默认产品ID和标签

### **示例5: 刷新Token + 自定义参数**
```bash
python agents/linkshare_agent/main.py \
  --refresh-token \
  --product-id 1731493745807886173 \
  --tags L_OEM1_XIAOMI_PUSH_ID L_OEM3_OPPO_PUSH_ID L_OEM2_VIVO_PUSH_ID
```
- 主动刷新token
- 使用指定的产品ID和标签

## 📊 **输出格式**

程序会按照用户要求的格式输出tracking links：

```
================================================================================
📊 Generated affiliate links for each sub id:
================================================================================

🔸 Link 1:
   Tag (Sub ID): L_OEM1_XIAOMI_PUSH_ID
   ^affiliate_sharing_links -> tracking link: https://www.tiktok.com/t/ZSShXXXXX/
   ^^affiliate_sharing_link -> short tracking link: https://www.tiktok.com/t/ZSShXXXXX/
      (Affiliate short link, domain: www.tiktok.com)

🔸 Link 2:
   Tag (Sub ID): L_OEM3_OPPO_PUSH_ID
   ^affiliate_sharing_links -> tracking link: https://www.tiktok.com/t/ZSShYYYYY/
   ^^affiliate_sharing_link -> short tracking link: https://www.tiktok.com/t/ZSShYYYYY/
      (Affiliate short link, domain: www.tiktok.com)

🔸 Link 3:
   Tag (Sub ID): L_OEM2_VIVO_PUSH_ID
   ^affiliate_sharing_links -> tracking link: https://www.tiktok.com/t/ZSShZZZZZ/
   ^^affiliate_sharing_link -> short tracking link: https://www.tiktok.com/t/ZSShZZZZZ/
      (Affiliate short link, domain: www.tiktok.com)

================================================================================
✅ 所有tracking links生成完成!
💡 每个链接都可以独立追踪佣金收益
```

## 🔧 **Token管理策略**

### **自动Token管理 (默认)**
- 程序会自动检查现有token的有效性
- 如果token仍然有效，直接使用
- 如果token过期，自动调用refresh API

### **主动Token刷新 (--refresh-token)**
- 强制调用refresh token API
- 获取全新的access token和refresh token
- 适用于:
  - 需要确保使用最新token
  - token即将过期时主动更新
  - 测试refresh token功能

## ⚠️ **注意事项**

1. **产品ID格式**: 必须是有效的TikTok Shop产品ID
2. **标签数量**: 建议不超过10个标签，避免API限制
3. **网络连接**: 确保能够访问TikTok Shop API端点
4. **Token有效性**: 确保refresh token仍在有效期内

## 🎯 **常见用法场景**

### **日常生产使用**
```bash
python agents/linkshare_agent/main.py --product-id YOUR_PRODUCT_ID
```

### **批量生成多个标签**
```bash
python agents/linkshare_agent/main.py \
  --product-id YOUR_PRODUCT_ID \
  --tags TAG1 TAG2 TAG3 TAG4 TAG5
```

### **Token维护**
```bash
python agents/linkshare_agent/main.py --refresh-token
```

### **测试新产品**
```bash
python agents/linkshare_agent/main.py \
  --product-id NEW_PRODUCT_ID \
  --tags TEST_TAG1 TEST_TAG2
```

## 🔍 **故障排除**

如果遇到问题，请按以下顺序检查：

1. **检查参数格式**: 确保产品ID和标签格式正确
2. **检查网络连接**: 确保能访问TikTok Shop API
3. **检查token状态**: 使用`--refresh-token`更新token
4. **查看错误日志**: 程序会输出详细的错误信息

## 📞 **获取帮助**
```bash
python agents/linkshare_agent/main.py --help
```

---

**系统已准备就绪，可以立即开始生产使用！** 🎉