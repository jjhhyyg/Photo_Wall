#!/bin/bash
# 照片墙本地测试启动脚本

echo "=========================================="
echo "  照片墙本地测试启动工具"
echo "=========================================="
echo ""

echo "请选择要启动的服务:"
echo "1. 同时启动照片墙和管理后台"
echo "2. 启动 Python 上传工具"
echo ""
read -p "请输入选项 (1-2): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动照片墙和管理后台..."
        
        if [ ! -f "config.public.json" ] || [ ! -f "config.private.json" ]; then
            echo "❌ 缺少必要配置文件，无法启动管理后台。"
            [ ! -f "config.public.json" ] && echo "   - 缺少: config.public.json"
            [ ! -f "config.private.json" ] && echo "   - 缺少: config.private.json"
            echo "💡 请先在项目根目录准备好配置文件后重试。"
            exit 1
        fi

        echo "📍 前端照片墙: http://localhost:8000"
        echo "📍 管理后台: http://localhost:8000/admin/"
        echo "⚠️  按 Ctrl+C 停止服务"
        echo ""
        echo "提示：请从项目根目录提供服务，这样后台可读取 config.public.json/config.private.json"
        echo ""
        python3 -m http.server 8000
        ;;
    2)
        echo ""
        echo "🚀 启动 Python 上传工具..."
        echo ""

        # 检查依赖
        if ! python3 -c "import oss2, tqdm, PIL" 2>/dev/null; then
            echo "❌ 缺少依赖库，正在安装..."
            pip3 install oss2 tqdm pillow
            echo ""
        fi

        python3 upload_to_oss.py
        ;;
    *)
        echo "❌ 无效的选项"
        exit 1
        ;;
esac
