#!/bin/bash
# 函数计算 API 测试脚本

echo "=========================================="
echo "  函数计算 API 测试工具"
echo "=========================================="
echo ""

# 读取配置文件
if [ ! -f "config.public.json" ]; then
    echo "❌ 配置文件 config.public.json 不存在！"
    exit 1
fi

# 使用 Python 解析 JSON（跨平台兼容）
GET_IMAGES_URL=$(python3 -c "import json; print(json.load(open('config.public.json'))['aliyun']['fc']['get_images_url'])")
UPLOAD_IMAGE_URL=$(python3 -c "import json; print(json.load(open('config.public.json'))['aliyun']['fc']['upload_image_url'])")
UPDATE_METADATA_URL=$(python3 -c "import json; print(json.load(open('config.public.json'))['aliyun']['fc']['update_metadata_url'])")

# 检查 URL 是否配置
if [[ "$GET_IMAGES_URL" == *"YOUR_"* ]]; then
    echo "❌ 请先在 config.public.json 中配置正确的 API 地址！"
    exit 1
fi

echo "📝 API 地址:"
echo "   获取图片列表: $GET_IMAGES_URL"
echo "   上传图片: $UPLOAD_IMAGE_URL"
echo "   更新元数据: $UPDATE_METADATA_URL"
echo ""

# 测试菜单
echo "请选择测试项目:"
echo "1. 测试获取图片列表 API"
echo "2. 测试上传图片 API（需要测试图片）"
echo "3. 测试更新元数据 API"
echo "4. 运行全部测试"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🧪 测试 1: 获取图片列表 API"
        echo "----------------------------------------"
        curl -s "${GET_IMAGES_URL}?limit=5&sort=date_desc" | python3 -m json.tool
        echo ""
        ;;
    2)
        echo ""
        echo "🧪 测试 2: 上传图片 API"
        echo "----------------------------------------"

        # 查找测试图片
        if [ -f "images/0.jpg" ]; then
            TEST_IMAGE="images/0.jpg"
        elif [ -f "readme_img/demo.jpg" ]; then
            TEST_IMAGE="readme_img/demo.jpg"
        else
            echo "❌ 找不到测试图片！请在 images/ 目录放置图片。"
            exit 1
        fi

        echo "📷 使用测试图片: $TEST_IMAGE"

        # macOS 和 Linux 的 base64 命令不同
        if [[ "$OSTYPE" == "darwin"* ]]; then
            IMAGE_BASE64=$(base64 -i "$TEST_IMAGE" | tr -d '\n')
        else
            IMAGE_BASE64=$(base64 -w 0 "$TEST_IMAGE")
        fi

        echo "📤 开始上传..."

        curl -s -X POST "$UPLOAD_IMAGE_URL" \
            -H "Content-Type: application/json" \
            -d "{
                \"filename\": \"test_upload_$(date +%s).jpg\",
                \"data\": \"data:image/jpeg;base64,$IMAGE_BASE64\",
                \"metadata\": {
                    \"note\": \"API 测试上传 - $(date)\"
                }
            }" | python3 -m json.tool

        echo ""
        ;;
    3)
        echo ""
        echo "🧪 测试 3: 更新元数据 API"
        echo "----------------------------------------"

        # 先获取第一张图片的文件名
        FIRST_IMAGE=$(curl -s "${GET_IMAGES_URL}?limit=1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data'][0]['filename'] if data['success'] and data['data'] else '')")

        if [ -z "$FIRST_IMAGE" ]; then
            echo "❌ 无法获取图片列表，请先确保 OSS 中有图片。"
            exit 1
        fi

        echo "📷 测试图片: $FIRST_IMAGE"
        echo "📝 更新元数据..."

        curl -s -X POST "$UPDATE_METADATA_URL" \
            -H "Content-Type: application/json" \
            -d "{
                \"filename\": \"$FIRST_IMAGE\",
                \"metadata\": {
                    \"date\": \"$(date +%Y-%m-%d)\",
                    \"time\": \"$(date +%H:%M:%S)\",
                    \"note\": \"API 测试更新 - $(date)\"
                }
            }" | python3 -m json.tool

        echo ""
        ;;
    4)
        echo ""
        echo "🧪 运行全部测试"
        echo "=========================================="

        # 测试 1
        echo ""
        echo "🧪 测试 1: 获取图片列表 API"
        echo "----------------------------------------"
        RESULT1=$(curl -s "${GET_IMAGES_URL}?limit=1")
        echo "$RESULT1" | python3 -m json.tool
        SUCCESS1=$(echo "$RESULT1" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))")

        if [ "$SUCCESS1" = "True" ]; then
            echo "✅ 测试 1 通过"
        else
            echo "❌ 测试 1 失败"
        fi

        # 测试 2 - 跳过（需要图片）
        echo ""
        echo "⏭️  测试 2: 上传图片 API（需要手动测试）"

        # 测试 3
        echo ""
        echo "🧪 测试 3: 更新元数据 API"
        echo "----------------------------------------"

        FIRST_IMAGE=$(echo "$RESULT1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data'][0]['filename'] if data['success'] and data['data'] else '')")

        if [ -n "$FIRST_IMAGE" ]; then
            RESULT3=$(curl -s -X POST "$UPDATE_METADATA_URL" \
                -H "Content-Type: application/json" \
                -d "{
                    \"filename\": \"$FIRST_IMAGE\",
                    \"metadata\": {
                        \"note\": \"批量测试 - $(date +%s)\"
                    }
                }")

            echo "$RESULT3" | python3 -m json.tool
            SUCCESS3=$(echo "$RESULT3" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))")

            if [ "$SUCCESS3" = "True" ]; then
                echo "✅ 测试 3 通过"
            else
                echo "❌ 测试 3 失败"
            fi
        else
            echo "⏭️  测试 3: 跳过（无可用图片）"
        fi

        echo ""
        echo "=========================================="
        echo "测试完成！"
        ;;
    *)
        echo "❌ 无效的选项"
        exit 1
        ;;
esac

echo ""
echo "✨ 测试完成！"
