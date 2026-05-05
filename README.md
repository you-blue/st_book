✨ AI驱动的小说角色卡与世界书生成器

🔍 **项目简介**
一个基于大语言模型（LLM）的自动化工具，智能提取中文小说文本中的角色信息和世界观设定，自动生成符合SillyTavern格式的高质量角色卡和结构化世界书。

🌟 **项目特点**
🔹 **高度自动化**: 一键式命令，全程无需人工干预
🔹 **两阶段处理**: "先提取，后升华"的智能工作流，保证最终产出质量
🔹 **高度可定制**: 通过config.yaml灵活配置AI行为
🔹 **模块化设计**: 代码结构清晰，易于维护和扩展

📁 **目录结构**
```
st_book/
├───character_extractor_llm.py  # 角色信息提取器
├───character_merger.py         # 角色信息合并器
├───character_workflow.py       # 主工作流管理器 (你的主要入口)
├───config_gui.py               # 可视化配置界面 (可选)
├───config_template.yaml        # 配置文件 (或模板)
├───create_card.py              # AI增强的角色卡生成器
├───project_config.py           # 项目配置加载器
├───README.md                   # 本文档
├───text_splitter.py            # 文本分割器
├───worldbook_extractor.py      # 世界书条目提取器
├───worldbook_generator.py      # AI增强的世界书生成器
├───一键启动.bat                 # 一键启动脚本
├───cards/                      # 【输出】最终生成的SillyTavern角色卡
├───chunks/                     # (中间) 小说文本分块
├───character_responses/        # (中间) 提取的原始角色信息
├───character_responses_bad/    # (中间) 失败的角色提取
├───character_responses_raw/    # (中间) 角色提取原始文本
├───roles_json/                 # (中间) 合并后的原始角色档案
├───wb_responses/               # (中间) 提取的原始世界书条目
└───worldbook/                  # 【输出】最终生成的结构化世界书
```

🚀 **快速开始**

1️⃣ **环境准备**
```bash
git clone https://github.com/nariahlamb/st_book.git
cd st_book
pip install -r requirements.txt
```

2️⃣ **配置设置**

方式一 — 可视化界面（推荐）：
```bash
python config_gui.py
```
双击 `一键启动.bat` 也可启动。

方式二 — 手动编辑：
```bash
cp config_template.yaml config.yaml
# 编辑 config_template.yaml 填入 API 密钥等配置
```

🔧 **配置示例**
```yaml
api:
  api_key: "YOUR_API_KEY_HERE"
  api_base: "https://api.openai.com/v1"
```

3️⃣ **执行命令**

🔹 **角色卡生成**:
```bash
python character_workflow.py auto
```

🔹 **世界书生成**:
```bash
python character_workflow.py wb-auto
```

📚 **核心模块说明**

🔹 **主要组件**:
- character_workflow.py: 主控制脚本
- config.yaml: 项目配置中心

🔹 **角色卡生成流程**:
1. text_splitter.py: 文本分割
2. character_extractor_llm.py: AI提取角色信息
3. character_merger.py: 信息合并
4. character_filter.py: 角色筛选
5. create_card.py: 高质量角色卡生成

🔹 **世界书生成流程**:
1. worldbook_extractor.py: 提取世界观设定
2. worldbook_generator.py: 生成结构化世界书

🛠️ **高级使用说明**

🔹 **分步执行命令**:
```bash
# 角色卡制作
python character_workflow.py split      # 分割文本
python character_workflow.py extract    # 提取角色
python character_workflow.py merge      # 合并角色
python character_workflow.py filter     # 筛选角色
python character_workflow.py create     # 生成角色卡

# 世界书制作
python character_workflow.py wb-extract    # 提取世界书条目
python character_workflow.py wb-generate   # 生成结构化世界书

# 工具命令
python character_workflow.py status     # 查看当前进度
python character_workflow.py clean      # 清理所有中间和输出文件
python character_workflow.py help       # 查看帮助信息

# GUI配置界面
python config_gui.py                    # 可视化编辑配置
```

⚙️ **配置说明**

🔹 **核心配置项**:
- API配置: api.api_key 和 api.api_base
- 模型选择: models.extraction_model 和 models.generation_model
- 温度参数: AI创作随机性控制
- 角色筛选: character_filter.keep_count

🔹 **输出目录**:
- cards/ - 最终角色卡文件
- worldbook/ - 最终世界书文件
- roles_json/ - 中间角色数据
- chunks/ - 分割文本块
- character_responses/ - 角色提取原始响应
- character_responses_bad/ - 失败的角色提取
- character_responses_raw/ - 角色提取原始文本
- wb_responses/ - 世界书提取响应

> 以上目录均可通过 `python character_workflow.py clean` 一键清理。

❗ **故障排除**
1. API调用失败: 检查API密钥和网络连接
2. 角色提取为空: 检查小说文本格式和编码
3. 内存不足: 调整text_processing.max_chunk_chars参数
4. 生成速度慢: 调整performance.max_concurrent参数

---

## 🛠️ 开发指南 (Development Guide)

### 📋 项目架构

本项目采用模块化设计，主要分为以下几个核心模块：

#### 🔧 核心工作流模块
- **character_workflow.py**: 主工作流控制器，统一管理所有子流程
- **project_config.py**: 统一配置管理，支持点记法访问配置项

#### 📝 文本处理模块
- **text_splitter.py**: 智能文本分割，支持多种分割策略
- **character_extractor_llm.py**: LLM驱动的角色信息提取
- **character_merger.py**: 角色信息智能合并与去重

#### 🌍 世界书模块
- **worldbook_extractor.py**: 世界观设定提取（支持事件+规则双重提取）
- **worldbook_generator.py**: 三层架构世界书生成器
- **worldbook_parameter_optimizer.py**: 世界书参数智能优化

#### 🎭 角色卡模块
- **create_card.py**: SillyTavern角色卡生成器
- **character_filter.py**: 角色筛选与质量控制

### 🏗️ 代码结构设计原则

#### 1. 配置驱动设计
所有模块都通过`project_config.py`获取配置，支持：
```python
# 点记法访问配置
config = get_config()
api_key = config.get("api.api_key")
temperature = config.get("models.extraction_temperature", 0.3)
```

#### 2. 异步并发处理
所有LLM调用都采用异步设计，支持：
- 并发控制：`asyncio.Semaphore`
- 重试机制：3次重试 + 智能延迟
- 限流处理：自动检测并递增延迟

#### 3. 错误处理与日志
统一的错误处理模式：
```python
for attempt in range(1, self.retry_limit + 1):
    try:
        # API调用
        return result
    except Exception as e:
        if "rate limit" in str(e).lower():
            await asyncio.sleep(self.retry_delay * attempt)
        elif attempt < self.retry_limit:
            await asyncio.sleep(self.retry_delay)
        else:
            # 创建fallback结果
            return fallback_result
```

### 📁 文件命名规范 (File Naming Convention)

#### 🐍 Python文件命名
- **模块文件**: `snake_case.py`
  - ✅ `character_extractor.py`
  - ✅ `worldbook_generator.py`
  - ❌ `CharacterExtractor.py`
  - ❌ `worldbook-generator.py`

- **测试文件**: `test_*.py`
  - ✅ `test_character_filter.py`
  - ✅ `test_retry_mechanism.py`

- **工具脚本**: `*_tool.py` 或 `*_utils.py`
  - ✅ `parameter_optimizer.py`
  - ✅ `config_validator.py`

#### 📂 目录命名
- **数据目录**: `snake_case/`
  - ✅ `character_responses/`
  - ✅ `wb_responses/`
  - ❌ `CharacterResponses/`

- **输出目录**: 简洁明了
  - ✅ `cards/`
  - ✅ `worldbook/`
  - ✅ `chunks/`

#### 📄 数据文件命名
- **配置文件**: `*.yaml` 或 `*.json`
  - ✅ `config.yaml`
  - ✅ `config_template.yaml`

- **数据文件**: `chunk_*.ext` 或 `*_data.ext`
  - ✅ `chunk_001.txt`
  - ✅ `chunk_001.json`
  - ✅ `mapping.json`

- **输出文件**: 描述性命名
  - ✅ `worldbook_st_v2.json`
  - ✅ `layered_worldbook.json`

#### 🏷️ 变量命名规范
- **函数名**: `snake_case`
  - ✅ `extract_characters()`
  - ✅ `generate_worldbook()`

- **类名**: `PascalCase`
  - ✅ `CharacterExtractor`
  - ✅ `WorldbookGenerator`

- **常量**: `UPPER_SNAKE_CASE`
  - ✅ `DEFAULT_CHUNK_SIZE`
  - ✅ `MAX_RETRY_ATTEMPTS`

- **配置键**: `snake_case` 或 `dot.notation`
  - ✅ `api.api_key`
  - ✅ `models.extraction_temperature`

### 🔄 开发工作流

#### 1. 添加新功能
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发并测试
python test_new_feature.py

# 3. 更新配置模板
# 在config.yaml中添加新的配置项

# 4. 更新文档
# 在README.md中添加使用说明
```

#### 2. 调试与测试
```bash
# 运行特定测试
python test_character_filter.py
python test_retry_mechanism.py

# 检查配置
python -c "from project_config import get_config; print(get_config().get('api.api_key'))"

# 验证工作流
python character_workflow.py status
```

#### 3. 性能优化
- **并发调优**: 调整`performance.max_concurrent`
- **重试策略**: 调整`performance.retry_limit`和`retry_delay`
- **内存优化**: 调整`text_processing.max_chunk_chars`

### 🧪 测试策略

#### 单元测试文件
- `test_character_filter.py`: 角色筛选功能测试
- `test_retry_mechanism.py`: 重试机制测试
- `test_parallel_extraction.py`: 并行提取测试
- `test_format_fix.py`: 格式识别测试

#### 集成测试
```bash
# 完整工作流测试
python character_workflow.py auto

# 世界书生成测试
python character_workflow.py wb-auto
```

### 📊 监控与日志

#### 日志级别
- `[SUCCESS]`: 操作成功完成
- `[PROCESS]`: 正在处理（包含重试次数）
- `[WARNING]`: 警告信息（重试失败）
- `[ERROR]`: 错误信息（最终失败）
- `[DEBUG]`: 调试信息

#### 性能监控
- 处理时间统计
- API调用次数统计
- 重试成功率统计
- 内存使用监控

---

## 🤝 贡献指南 (Contributing)

### 提交代码前检查清单
- [ ] 代码遵循命名规范
- [ ] 添加了适当的错误处理和重试机制
- [ ] 更新了相关的配置模板
- [ ] 编写了对应的测试文件
- [ ] 更新了README文档

### 问题报告
提交Issue时请包含：
1. 详细的错误信息和日志
2. 配置文件（去除敏感信息）
3. 复现步骤
4. 系统环境信息

欢迎提交Issue和Pull Request来改进项目！

---

## 📄 许可证 (License)
本项目采用MIT许可证。
