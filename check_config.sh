#!/bin/bash
# 配置文件检查脚本

echo "=========================================="
echo "  配置文件检查工具"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

check_file() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $2 存在"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌${NC} $2 不存在"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_json() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if python3 -m json.tool "$1" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $2 格式正确"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌${NC} $2 格式错误"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_config_value() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    VALUE=$(python3 -c "import json; print(json.load(open('$1'))$2)" 2>/dev/null)

    if [ -z "$VALUE" ]; then
        echo -e "${RED}❌${NC} $3 未配置"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    elif [[ "$VALUE" == *"YOUR_"* ]]; then
        echo -e "${YELLOW}⚠️${NC}  $3 = $VALUE (需要替换)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        return 2
    else
        echo -e "${GREEN}✅${NC} $3 已配置"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    fi
}

echo "📋 1. 检查配置文件是否存在"
echo "----------------------------------------"
check_file "config.public.json" "config.public.json"
check_file "config.public.example.json" "config.public.example.json"
check_file "config.private.json" "config.private.json"
check_file "config.private.example.json" "config.private.example.json"
echo ""

echo "📋 2. 检查 JSON 格式"
echo "----------------------------------------"
if [ -f "config.public.json" ]; then
    check_json "config.public.json" "config.public.json"
fi

if [ -f "config.private.json" ]; then
    check_json "config.private.json" "config.private.json"
fi
echo ""

echo "📋 3. 检查 config.public.json 配置项"
echo "----------------------------------------"
if [ -f "config.public.json" ]; then
    check_config_value "config.public.json" "['aliyun']['fc']['get_images_url']" "获取图片列表 API"
    check_config_value "config.public.json" "['aliyun']['fc']['upload_image_url']" "上传图片 API"
    check_config_value "config.public.json" "['aliyun']['fc']['update_metadata_url']" "更新元数据 API"
fi
echo ""

echo "📋 4. 检查 config.private.json 配置项"
echo "----------------------------------------"
if [ -f "config.private.json" ]; then
    check_config_value "config.private.json" "['aliyun']['access_key_id']" "AccessKey ID"
    check_config_value "config.private.json" "['aliyun']['access_key_secret']" "AccessKey Secret"
    check_config_value "config.private.json" "['aliyun']['oss']['bucket_name']" "OSS Bucket 名称"
    check_config_value "config.private.json" "['aliyun']['oss']['endpoint']" "OSS 接入点"
fi
echo ""

echo "📋 5. 检查项目文件"
echo "----------------------------------------"
check_file "index.html" "前端页面"
check_file "script_oss.js" "前端脚本"
check_file "styles.css" "样式文件"
check_file "upload_to_oss.py" "上传工具"
check_file "admin/index.html" "管理后台页面"
check_file "admin/admin.js" "管理后台脚本"
echo ""

echo "📋 6. 检查 Python 依赖"
echo "----------------------------------------"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if python3 -c "import oss2" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} oss2 已安装"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}❌${NC} oss2 未安装"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if python3 -c "import tqdm" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} tqdm 已安装"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}❌${NC} tqdm 未安装"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if python3 -c "import PIL" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} Pillow 已安装"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}❌${NC} Pillow 未安装"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

echo "=========================================="
echo "  检查结果汇总"
echo "=========================================="
echo "总检查项: $TOTAL_CHECKS"
echo -e "${GREEN}通过: $PASSED_CHECKS${NC}"
if [ $WARNING_CHECKS -gt 0 ]; then
    echo -e "${YELLOW}警告: $WARNING_CHECKS${NC}"
fi
if [ $FAILED_CHECKS -gt 0 ]; then
    echo -e "${RED}失败: $FAILED_CHECKS${NC}"
fi
echo ""

if [ $FAILED_CHECKS -eq 0 ] && [ $WARNING_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！可以开始测试。${NC}"
    exit 0
elif [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  有警告项需要处理。${NC}"
    echo ""
    echo "建议操作："
    echo "1. 打开 config.public.json 和 config.private.json"
    echo "2. 将所有 YOUR_* 占位符替换为实际值"
    exit 1
else
    echo -e "${RED}❌ 有失败项需要修复。${NC}"
    echo ""
    echo "建议操作："
    if [ ! -f "config.public.json" ]; then
        echo "• 复制示例配置: cp config.public.example.json config.public.json"
    fi
    if [ ! -f "config.private.json" ]; then
        echo "• 复制示例配置: cp config.private.example.json config.private.json"
    fi

    if ! python3 -c "import oss2, tqdm, PIL" 2>/dev/null; then
        echo "• 安装 Python 依赖: pip3 install oss2 tqdm pillow"
    fi
    exit 1
fi
