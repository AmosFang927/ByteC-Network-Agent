#!/usr/bin/env python3
"""
Data Input Agent 使用示例
演示如何使用数据导入功能
"""

import subprocess
import sys
from pathlib import Path

def run_example():
    """运行示例"""
    print("🚀 Data Input Agent 使用示例")
    print("=" * 50)
    
    # 1. 创建示例数据
    print("\n1️⃣ 创建示例数据...")
    try:
        result = subprocess.run([
            sys.executable, "agents/data_input_agent/create_sample_data.py"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 示例数据创建成功")
        else:
            print(f"❌ 示例数据创建失败: {result.stderr}")
            return
    except Exception as e:
        print(f"❌ 创建示例数据时出错: {e}")
        return
    
    # 2. 正常模式处理
    print("\n2️⃣ 正常模式处理（插入Cloud SQL）...")
    try:
        result = subprocess.run([
            sys.executable, "agents/data_input_agent/data_importer.py",
            "--import", "sample_conversion_data.xlsx"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 正常模式处理成功")
            print(f"输出: {result.stdout}")
        else:
            print(f"❌ 正常模式处理失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 正常模式处理时出错: {e}")
    
    # 3. Passthrough模式处理
    print("\n3️⃣ Passthrough模式处理（仅输出Excel）...")
    try:
        result = subprocess.run([
            sys.executable, "agents/data_input_agent/data_importer.py",
            "--import", "sample_conversion_data.xlsx",
            "--passthrough"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Passthrough模式处理成功")
            print(f"输出: {result.stdout}")
        else:
            print(f"❌ Passthrough模式处理失败: {result.stderr}")
    except Exception as e:
        print(f"❌ Passthrough模式处理时出错: {e}")
    
    # 4. 检查输出文件
    print("\n4️⃣ 检查输出文件...")
    output_dir = Path("output")
    if output_dir.exists():
        files = list(output_dir.glob("*.xlsx"))
        print(f"📁 输出目录中找到 {len(files)} 个Excel文件:")
        for file in files:
            print(f"  - {file.name}")
    else:
        print("❌ 输出目录不存在")
    
    print("\n🎉 示例运行完成！")

def show_help():
    """显示帮助信息"""
    print("""
📖 Data Input Agent 使用说明

🔧 基本用法:
  python agents/data_input_agent/data_importer.py --import <文件名>

🔧 参数说明:
  --import <文件名>    指定要导入的Excel文件名（必需）
  --passthrough       启用passthrough模式，不插入Cloud SQL

🔧 示例:
  # 正常模式（插入Cloud SQL）
  python agents/data_input_agent/data_importer.py --import sample_conversion_data.xlsx
  
  # Passthrough模式（仅输出Excel）
  python agents/data_input_agent/data_importer.py --import sample_conversion_data.xlsx --passthrough

🔧 创建示例数据:
  python agents/data_input_agent/create_sample_data.py

📁 文件结构:
  input/                    # 输入文件目录
  output/                   # 输出文件目录
  agents/data_input_agent/  # 处理器代码

⚙️ 配置项:
  在 config.py 中配置 INPUT_DATA_REMOVE_COLUMNS 等参数
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_help()
    else:
        run_example() 