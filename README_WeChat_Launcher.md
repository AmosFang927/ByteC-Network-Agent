# 微信分身啟動器

這是一套用於在 macOS 上自動啟動微信分身的 bash 腳本工具。

## 📁 文件說明

### 核心腳本
- `wechat_clone_launcher.sh` - 基礎微信分身啟動腳本
- `wechat_multi_clone_launcher.sh` - 進階多分身啟動腳本
- `setup_wechat_launch_agent.sh` - 設置登入時自動啟動的安裝腳本

## 🚀 快速開始

### 1. 安裝自動啟動

```bash
# 設置登入時自動啟動
./setup_wechat_launch_agent.sh install
```

### 2. 手動測試

```bash
# 測試啟動腳本
./wechat_multi_clone_launcher.sh

# 查看幫助
./wechat_multi_clone_launcher.sh --help

# 列出配置的分身
./wechat_multi_clone_launcher.sh -l

# 啟動單個分身
./wechat_multi_clone_launcher.sh -s personal
```

### 3. 檢查狀態

```bash
# 檢查安裝狀態
./setup_wechat_launch_agent.sh status

# 測試腳本功能
./setup_wechat_launch_agent.sh test
```

## ⚙️ 配置說明

### 分身配置

在 `wechat_multi_clone_launcher.sh` 中修改 `CLONE_CONFIGS` 數組：

```bash
CLONE_CONFIGS=(
    "personal"    # 個人微信
    "work"        # 工作微信
    "business"    # 商務微信
    "test"        # 測試微信
)
```

### 日誌文件

- 主日誌：`$HOME/wechat_multi_clone_launcher.log`
- 標準輸出：`$HOME/wechat_launcher_stdout.log`
- 標準錯誤：`$HOME/wechat_launcher_stderr.log`

## 🔧 功能特性

### ✅ 已實現功能

1. **多分身支持** - 可同時啟動多個微信分身
2. **自動檢測** - 避免重複啟動已運行的分身
3. **網絡檢查** - 啟動前檢查網絡連接
4. **日誌記錄** - 詳細的啟動日誌記錄
5. **錯誤處理** - 完善的錯誤處理機制
6. **登入自啟** - 設置為登入時自動啟動
7. **狀態監控** - 可查看運行狀態

### 🎯 使用場景

- **個人使用** - 分離個人和工作微信
- **多賬號管理** - 同時管理多個微信賬號
- **自動化工作流** - 登入後自動啟動所需應用

## 📋 命令參考

### 設置腳本命令

```bash
./setup_wechat_launch_agent.sh install    # 安裝自動啟動
./setup_wechat_launch_agent.sh uninstall  # 卸載自動啟動
./setup_wechat_launch_agent.sh status     # 檢查狀態
./setup_wechat_launch_agent.sh test       # 測試腳本
./setup_wechat_launch_agent.sh help       # 顯示幫助
```

### 啟動腳本命令

```bash
./wechat_multi_clone_launcher.sh          # 啟動所有分身
./wechat_multi_clone_launcher.sh -l       # 列出分身配置
./wechat_multi_clone_launcher.sh -s name  # 啟動指定分身
./wechat_multi_clone_launcher.sh --help   # 顯示幫助
```

## 🔍 故障排除

### 常見問題

1. **微信未啟動**
   - 檢查微信是否已安裝在 `/Applications/WeChat.app`
   - 確認腳本有執行權限：`chmod +x *.sh`

2. **LaunchAgent 未載入**
   - 檢查 LaunchAgent 狀態：`launchctl list | grep wechat`
   - 手動載入：`launchctl load ~/Library/LaunchAgents/com.bytec.wechatlauncher.plist`

3. **權限問題**
   - 確保腳本有執行權限
   - 檢查 LaunchAgents 目錄權限

4. **日誌查看**
   ```bash
   # 查看主日誌
   tail -f ~/wechat_multi_clone_launcher.log
   
   # 查看標準輸出
   tail -f ~/wechat_launcher_stdout.log
   
   # 查看錯誤日誌
   tail -f ~/wechat_launcher_stderr.log
   ```

### 手動調試

```bash
# 直接運行腳本查看輸出
./wechat_multi_clone_launcher.sh

# 檢查 LaunchAgent 配置
cat ~/Library/LaunchAgents/com.bytec.wechatlauncher.plist

# 檢查進程
ps aux | grep WeChat
```

## 🛠️ 自定義配置

### 修改啟動延遲

在 `wechat_multi_clone_launcher.sh` 中修改：

```bash
# 分身之間間隔啟動時間（秒）
sleep 2

# 單個分身啟動等待時間（秒）
sleep 5
```

### 修改日誌輪換大小

```bash
# 日誌文件最大大小（字節）
local max_log_size=10485760  # 10MB
```

### 添加新的分身

1. 在 `CLONE_CONFIGS` 數組中添加新名稱
2. 確保微信應用程序支持該配置
3. 重新安裝 LaunchAgent

## 📝 注意事項

1. **微信版本** - 確保使用最新版本的微信
2. **系統權限** - 可能需要授予輔助功能權限
3. **網絡要求** - 需要穩定的網絡連接
4. **存儲空間** - 多分身會佔用更多存儲空間
5. **性能影響** - 多個微信可能影響系統性能

## 🔄 更新日誌

### v1.0.0
- 初始版本
- 支持多分身啟動
- 登入時自動啟動
- 完整的日誌記錄
- 錯誤處理機制

## 📞 支持

如有問題或建議，請檢查日誌文件或聯繫開發者。

---

**作者**: ByteC Network Agent  
**版本**: 1.0.0  
**更新日期**: 2024年12月 