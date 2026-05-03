# AI驱动的小说角色卡与世界书生成器

## 项目简介
一个基于大语言模型（LLM）的自动化工具，智能提取中文小说文本中的角色信息和世界观设定，自动生成符合SillyTavern格式的高质量角色卡和结构化世界书。

## 项目特点
- **高度自动化**: 一键式命令，全程无需人工干预
- **两阶段处理**: "先提取，后升华"的智能工作流，保证最终产出质量
- **高度可定制**: 通过config.yaml灵活配置AI行为，支持GUI可视化编辑
- **模块化设计**: 代码结构清晰，易于维护和扩展

## 目录结构

```
st_book/
├── character_workflow.py           # 主工作流管理器 (主要入口)
├── config_gui.py                   # 可视化配置界面 (tkinter)
├── project_config.py               # 统一配置加载器
├── text_splitter.py                # 文本分割器
├── character_extractor_llm.py      # AI角色信息提取器
├── character_merger.py             # 角色信息合并器
├── character_filter.py             # 角色筛选与质量控制
├── create_card.py                  # AI角色卡生成器
├── worldbook_extractor.py          # 世界书条目提取器
├── worldbook_classifier.py         # 世界书数据分类器
├── worldbook_generator.py          # 世界书生成器 (三层架构)
├── code.py                         # SillyTavern V2格式转换
├── config_template.yaml            # 配置文件模板
├── requirements.txt                # Python依赖
├── 一键启动.bat                    # 一键启动脚本
│
├── {小说名}/cards/                 # 【输出】角色卡 (以小说名命名)
├── {小说名}/worldbook/             # 【输出】世界书 (以小说名命名)
├── cards/                          # (中间/输出) 角色卡原始目录
├── worldbook/                      # (中间/输出) 世界书原始目录
├── chunks/                         # (中间) 文本分块
├── character_responses/            # (中间) 原始角色信息
├── character_responses_bad/        # (中间) 失败的角色提取
├── character_responses_raw/        # (中间) 角色提取原始文本
├── roles_json/                     # (中间) 合并后的角色档案
├── wb_responses/                   # (中间) 世界书提取条目
└── .venv/                          # Python虚拟环境
```

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/nariahlamb/st_book.git
cd st_book

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

**方式一 — 可视化界面（推荐）**：
```bash
python config_gui.py
```
双击 `一键启动.bat` 也可启动。

**方式二 — 手动编辑**：
```bash
cp config_template.yaml config.yaml
# 编辑 config.yaml 填入 API 密钥等配置
```

### 3. 执行命令

```bash
# 一键全自动（角色卡 + 世界书）
python character_workflow.py full-auto

# 仅角色卡
python character_workflow.py auto

# 仅世界书
python character_workflow.py wb-auto
```

## 可视化配置界面

内置 tkinter GUI，无需手动编辑 YAML：

- **加载小说** — 选择源文件(.txt)路径和编码
- **API & 模型** — API密钥/URL，提取/生成模型
- **模型参数** — 温度、Token限制、超时等
- **网络与性能** — 并发数、重试次数、限流延迟
- **缓存配置** — 启用缓存、目录、过期天数
- **输出目录** — 各中间产物输出位置、角色筛选数量

工作流按钮按三行排列（角色卡 / 世界书 / 通用），悬浮显示说明。

## 工作流详细说明

### 角色卡生成流程
1. **文本分割** — 将小说按大小分割为文本块
2. **角色提取** — LLM从各文本块中提取角色信息
3. **角色合并** — 智能合并重复的角色数据（基于名称和内容相似度）
4. **角色筛选** — 按内容丰富度保留前N个角色（数量可在GUI配置）
5. **角色卡生成** — AI生成SillyTavern V2格式的角色卡

### 世界书生成流程
1. **文本分割** — 复用角色卡流程的分块结果
2. **条目提取** — 提取世界观设定条目（事件/规则双通道）
3. **条目分类** — 自动分类（规则层/事件层/实体层）
4. **世界书生成** — 支持三层架构 / 事件驱动 / 传统三种模式

### 输出保存
- 最终角色卡自动保存到 `{小说名}/cards/`
- 最终世界书自动保存到 `{小说名}/worldbook/`
- `clean` 命令仅清理中间目录，保留以小说命名的输出文件夹

## 命令参考

| 命令 | 说明 |
|------|------|
| `full-auto` | 【推荐】一键全自动：角色卡 + 世界书 |
| `auto` | 角色全自动：清理并运行角色卡流程 |
| `wb-auto` | 世界书全自动：清理并运行世界书流程 |
| `full` | 完整流程（不清理，直接运行） |
| `split` | 仅分割文本 |
| `extract` | 仅提取角色信息 |
| `merge` | 仅合并角色数据 |
| `filter` | 仅筛选角色 |
| `create` | 仅生成角色卡 |
| `wb-extract` | 仅提取世界书条目 |
| `wb-generate` | 仅生成世界书 |
| `status` | 查看工作流状态 |
| `clean` | 清理中间文件 |
| `help` | 显示帮助信息 |

## 配置项

### 核心配置
- `api.api_key` / `api.api_base` — API连接
- `models.extraction_model` / `models.generation_model` — 模型选择
- `models.extraction_temperature` / `models.generation_temperature` — 创作随机性
- `character_filter.keep_count` — 角色筛选保留数量
- `performance.max_concurrent` — 并发请求数

### 输出目录
- `input.source_file` — 源小说文件路径
- `output.cards_dir` / `output.worldbook_dir` — 输出位置
- `cache.cache_dir` — 缓存目录

## 技术特性

- **自动虚拟环境** — 脚本自动检测并使用 `.venv/` 下的 Python 解释器
- **编码兼容** — 自动处理 UTF-8/GBK 编码，支持 emoji 日志输出
- **并行处理** — 异步并发 + 信号量控制，支持批量 API 调用
- **智能重试** — 自动检测限流，指数退避重试
- **缓存机制** — 避免重复 API 调用，可配置过期时间
- **YAML 格式保留** — 使用 ruamel.yaml 保留配置注释和格式

## 依赖

```
openai>=1.0.0            # LLM API 调用
pyyaml>=6.0              # YAML 配置解析
ruamel.yaml>=0.18.0      # 保留注释的 YAML 读写
opencc-python-reimplemented>=0.1.7  # 简繁转换
```

## 故障排除

1. **API调用失败** — 检查API密钥和网络连接，确认API地址正确
2. **角色提取为空** — 检查小说文本格式和编码（推荐 UTF-8）
3. **内存不足** — 调整 `text_processing.max_chunk_chars` 减小分块大小
4. **生成速度慢** — 调整 `performance.max_concurrent` 增加并发数
5. **模块缺失** — 确保在虚拟环境中运行，已安装 `requirements.txt`
6. **编码错误** — GUI 和 CLI 均已强制 UTF-8 输出，避免 GBK 报错

---

## 开发指南

### 核心模块

- **character_workflow.py**: 主工作流控制器
- **project_config.py**: 统一配置管理，支持点记法
- **text_splitter.py**: 智能文本分割
- **character_extractor_llm.py**: LLM角色信息提取
- **character_merger.py**: 角色信息合并与去重
- **character_filter.py**: 角色筛选与质量控制
- **create_card.py**: SillyTavern角色卡生成
- **worldbook_extractor.py**: 世界观设定提取
- **worldbook_classifier.py**: 世界书条目分类
- **worldbook_generator.py**: 三层架构世界书生成
- **code.py**: SillyTavern V2格式转换
- **config_gui.py**: tkinter可视化配置

### 代码设计原则

#### 配置驱动
所有模块通过 `project_config.get_config()` 获取配置：
```python
config = get_config()
api_key = config.get("api.api_key")
keep_count = config.get("character_filter.keep_count", 30)
```

#### 异步并发
所有LLM调用采用异步设计：
- 并发控制：`asyncio.Semaphore`
- 重试机制：`retry_limit` + 递增延迟
- 限流处理：自动检测并延迟

#### 错误处理
```python
for attempt in range(1, retry_limit + 1):
    try:
        return await api_call()
    except Exception as e:
        if "rate limit" in str(e).lower():
            await asyncio.sleep(delay * attempt)
        elif attempt < retry_limit:
            await asyncio.sleep(delay)
```

### 测试

```bash
# 单元测试
python test_character_filter.py
python test_retry_mechanism.py

# 集成测试
python character_workflow.py status
```

---

## 许可证
本项目采用MIT许可证。
