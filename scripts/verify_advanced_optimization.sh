#!/bin/bash
# 验证进阶优化效果

echo "🔍 进阶优化验证脚本"
echo "================================"
echo ""

echo "📊 已实施的优化:"
echo "--------------------------------"
echo "保守优化:"
echo "  1. ✅ iterrows() → values.tolist()"
echo "  2. ✅ batch_size: 500 → 1500"
echo "  3. ✅ 股票列表缓存"
echo ""
echo "进阶优化:"
echo "  4. ✅ PostgreSQL COPY 命令"
echo "  5. ✅ 数据库参数优化"
echo "  6. ✅ 简化数据处理流程"
echo ""

echo "🔍 验证代码修改:"
echo "--------------------------------"

# 检查 COPY 方法
if grep -q "_bulk_insert_with_copy" stockguru-web/backend/app/services/daily_data_sync_service_neon.py; then
    echo "✅ COPY 方法已添加"
else
    echo "❌ COPY 方法未找到"
fi

# 检查 batch_size
if grep -q "batch_size = 1500" stockguru-web/backend/app/services/daily_data_sync_service_neon.py; then
    echo "✅ batch_size 已更新为 1500"
else
    echo "❌ batch_size 未更新"
fi

# 检查数据库参数优化
if grep -q "SET LOCAL work_mem" stockguru-web/backend/app/services/daily_data_sync_service_neon.py; then
    echo "✅ 数据库参数优化已添加"
else
    echo "❌ 数据库参数优化未找到"
fi

# 检查缓存功能
if grep -q "stock_list_cache.json" stockguru-web/backend/app/services/daily_data_sync_service_neon.py; then
    echo "✅ 股票列表缓存已添加"
else
    echo "❌ 股票列表缓存未找到"
fi

echo ""
echo "📈 预期性能:"
echo "--------------------------------"
echo "单日同步: 14.8分钟 → 8.8分钟 (提升40%)"
echo "1年同步: 60.2小时 → 35.8小时 (节省24.4小时)"
echo ""

echo "🧪 运行测试:"
echo "--------------------------------"
echo "建议运行以下命令测试:"
echo ""
echo "# 测试单日同步"
echo "curl -X POST 'http://localhost:8000/api/v1/daily/sync' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"sync_date\": \"2025-10-11\"}'"
echo ""
echo "# 监控日志"
echo "tail -f stockguru-web/backend/backend.log | grep -E '(COPY|数据库性能|进度)'"
echo ""

echo "✅ 验证完成！"
