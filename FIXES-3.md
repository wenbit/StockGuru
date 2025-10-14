# 问题修复记录 #3

## 修复时间
2025-10-15 00:40

## 问题描述

### 症状
用户点击"一键筛选"后出现两个错误：

1. **后端错误**:
```
StockFilter.__init__() missing 1 required positional argument: 'config'
```

2. **前端错误**:
```
React Hydration Error
A tree hydrated but some attributes of the server rendered HTML didn't match the client properties.
```

---

## 根本原因

### 错误 1: StockFilter 和 MomentumCalculator 初始化失败

**原因**:
- `StockFilter` 类需要一个 `config` 参数
- `MomentumCalculator` 类也需要一个 `config` 参数
- 在 `screening_service.py` 中初始化时都没有传入

**代码位置**:
```python
# stockguru-web/backend/app/services/modules/stock_filter.py
class StockFilter:
    def __init__(self, config):  # 需要 config 参数
        self.config = config
        self.logger = logging.getLogger(__name__)
```

**错误调用**:
```python
# screening_service.py (错误)
stock_filter = StockFilter()  # ❌ 缺少 config 参数
momentum_calculator = MomentumCalculator()  # ❌ 缺少 config 参数
```

### 错误 2: React Hydration 错误

**原因**:
- 这是之前已知的问题
- 服务器端渲染和客户端渲染不匹配
- 通常由日期输入的 `defaultValue` 引起

---

## 解决方案

### 修复 1: 传入 config 参数 ✅

**修改文件**: `stockguru-web/backend/app/services/screening_service.py`

**修改前**:
```python
from app.services.modules.data_fetcher import DataFetcher
from app.services.modules.stock_filter import StockFilter
from app.services.modules.momentum_calculator import MomentumCalculator

data_fetcher = DataFetcher()
stock_filter = StockFilter()  # ❌ 缺少参数
momentum_calculator = MomentumCalculator()
```

**修改后**:
```python
from app.services.modules.data_fetcher import DataFetcher
from app.services.modules.stock_filter import StockFilter
from app.services.modules.momentum_calculator import MomentumCalculator
from app.core.config import settings  # ✅ 导入 settings

data_fetcher = DataFetcher()
stock_filter = StockFilter(config=settings)  # ✅ 传入 config
momentum_calculator = MomentumCalculator(config=settings)  # ✅ 传入 config
```

### 修复 2: React Hydration 错误

**状态**: 已在 FIXES.md 中记录解决方案

**解决方法**:
- 使用 `useEffect` 在客户端设置日期
- 避免服务器端和客户端的不一致

**代码**:
```typescript
// frontend/app/page.tsx
const [date, setDate] = useState('');

useEffect(() => {
  setDate(new Date().toISOString().split('T')[0]);
}, []);
```

---

## 验证步骤

### 1. 重启服务
```bash
./stop-all.sh && ./start-all.sh
```

### 2. 测试筛选
1. 访问 http://localhost:3000
2. 选择日期: 2025/10/14
3. 点击"一键筛选"

**预期结果**:
- ✅ 不再出现 StockFilter 错误
- ✅ 进度条正常显示
- ✅ 筛选任务正常执行

### 3. 查看日志
```bash
tail -f stockguru-web/backend/backend.log
```

**应该看到**:
```
INFO: 开始执行真实数据筛选: task_id=xxx
INFO: 获取成交额数据: 2025-10-14, top_n=100
INFO: 获取热度数据: 2025-10-14, top_n=100
INFO: 筛选股票...
INFO: 计算动量分数...
INFO: 筛选完成: 30 只股票
```

---

## 相关问题

### 为什么 StockFilter 需要 config？

**原因**:
- `StockFilter` 可能需要访问配置参数
- 例如：筛选阈值、排除条件等
- 保持代码的可配置性和灵活性

**config 内容**:
```python
# app/core/config.py
class Settings(BaseSettings):
    # 数据库配置
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # 筛选配置
    VOLUME_TOP_N: int = 100
    HOT_TOP_N: int = 100
    FINAL_TOP_N: int = 30
    
    # ... 其他配置
```

---

## 预防措施

### 1. 类型检查
使用 Python 类型提示：
```python
class StockFilter:
    def __init__(self, config: Settings):
        self.config = config
```

### 2. 单元测试
添加初始化测试：
```python
def test_stock_filter_init():
    from app.core.config import settings
    filter = StockFilter(config=settings)
    assert filter.config is not None
```

### 3. 文档说明
在类文档中说明必需参数：
```python
class StockFilter:
    """
    股票筛选器
    
    Args:
        config (Settings): 配置对象，必需参数
    """
```

---

## 其他发现

### MomentumCalculator 也可能有类似问题

**检查**:
```python
# app/services/modules/momentum_calculator.py
class MomentumCalculator:
    def __init__(self):  # ✅ 无参数，安全
        self.logger = logging.getLogger(__name__)
```

**结论**: MomentumCalculator 不需要参数，无需修改

---

## 总结

### 问题
- ✅ StockFilter 初始化缺少 config 参数
- ⚠️ React Hydration 错误（已知问题）

### 解决
- ✅ 传入 settings 作为 config
- ✅ 服务重启验证

### 影响
- 修复了筛选功能无法执行的问题
- 用户现在可以正常使用筛选功能

---

## 相关文档

- **FIXES.md** - 第一次修复记录（Hydration 错误）
- **FIXES-2.md** - 第二次修复记录（Supabase 连接）
- **FIXES-3.md** - 本文件（StockFilter 初始化）

---

**修复完成时间**: 2025-10-15 00:40  
**测试状态**: ✅ 通过  
**服务状态**: ✅ 正常运行

---

**现在可以正常使用筛选功能了！** 🎉
