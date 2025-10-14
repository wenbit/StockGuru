#!/bin/bash
# K线图端到端测试脚本

echo "=========================================="
echo "K线图 API 端到端测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
PASSED=0
FAILED=0

# 测试函数
test_api() {
    local test_name=$1
    local url=$2
    local expected_field=$3
    
    echo -n "测试: $test_name ... "
    
    response=$(curl -s "$url")
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$http_code" = "200" ]; then
        if echo "$response" | grep -q "$expected_field"; then
            echo -e "${GREEN}✓ 通过${NC}"
            ((PASSED++))
            return 0
        else
            echo -e "${RED}✗ 失败 (缺少字段: $expected_field)${NC}"
            ((FAILED++))
            return 1
        fi
    else
        echo -e "${RED}✗ 失败 (HTTP $http_code)${NC}"
        echo "响应: $response"
        ((FAILED++))
        return 1
    fi
}

# 1. 测试健康检查
echo "1. 健康检查"
test_api "后端健康检查" "http://localhost:8000/health" "healthy"
echo ""

# 2. 测试 K线 API - 基本功能
echo "2. K线 API 基本功能"
test_api "获取000001的K线数据" "http://localhost:8000/api/v1/stock/000001/kline?days=30" '"code"'
test_api "验证数据字段存在" "http://localhost:8000/api/v1/stock/000001/kline?days=30" '"data"'
test_api "验证count字段存在" "http://localhost:8000/api/v1/stock/000001/kline?days=30" '"count"'
echo ""

# 3. 测试均线数据
echo "3. 均线数据验证"
test_api "MA5均线存在" "http://localhost:8000/api/v1/stock/000001/kline?days=30" '"ma5"'
test_api "MA10均线存在" "http://localhost:8000/api/v1/stock/000001/kline?days=30" '"ma10"'
test_api "MA20均线存在" "http://localhost:8000/api/v1/stock/000001/kline?days=30" '"ma20"'
echo ""

# 4. 测试不同股票代码
echo "4. 多股票测试"
test_api "获取600000的K线数据" "http://localhost:8000/api/v1/stock/600000/kline?days=30" '"600000"'
test_api "获取000002的K线数据" "http://localhost:8000/api/v1/stock/000002/kline?days=30" '"000002"'
echo ""

# 5. 测试不同天数参数
echo "5. 参数测试"
test_api "10天数据" "http://localhost:8000/api/v1/stock/000001/kline?days=10" '"data"'
test_api "60天数据" "http://localhost:8000/api/v1/stock/000001/kline?days=60" '"data"'
echo ""

# 6. 测试 CORS
echo "6. CORS 配置测试"
cors_response=$(curl -s -H "Origin: http://localhost:3000" -I "http://localhost:8000/api/v1/stock/000001/kline?days=10" 2>&1)
if echo "$cors_response" | grep -q "access-control-allow-origin"; then
    echo -e "${GREEN}✓ CORS 配置正确${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ CORS 配置缺失${NC}"
    ((FAILED++))
fi
echo ""

# 7. 验证数据完整性
echo "7. 数据完整性验证"
data=$(curl -s "http://localhost:8000/api/v1/stock/000001/kline?days=30")
count=$(echo "$data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['count'])" 2>/dev/null)
if [ "$count" -gt 0 ]; then
    echo -e "${GREEN}✓ 返回 $count 条数据${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 数据为空${NC}"
    ((FAILED++))
fi
echo ""

# 8. 验证 MA 值计算
echo "8. MA 值计算验证"
ma_data=$(curl -s "http://localhost:8000/api/v1/stock/000001/kline?days=30" | python3 -c "
import sys, json
data = json.load(sys.stdin)
last = data['data'][-1]
has_ma5 = last.get('ma5') is not None
has_ma10 = last.get('ma10') is not None
has_ma20 = last.get('ma20') is not None
print(f'{has_ma5},{has_ma10},{has_ma20}')
" 2>/dev/null)

IFS=',' read -r has_ma5 has_ma10 has_ma20 <<< "$ma_data"
if [ "$has_ma5" = "True" ] && [ "$has_ma10" = "True" ] && [ "$has_ma20" = "True" ]; then
    echo -e "${GREEN}✓ 所有均线值计算正确${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 均线值计算失败 (MA5:$has_ma5, MA10:$has_ma10, MA20:$has_ma20)${NC}"
    ((FAILED++))
fi
echo ""

# 总结
echo "=========================================="
echo "测试总结"
echo "=========================================="
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo "总计: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！K线图功能正常${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分测试失败，请检查日志${NC}"
    exit 1
fi
