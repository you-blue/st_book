#!/usr/bin/env python3
"""
角色工作流管理器 - 统一管理角色提取和合并流程
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
import time
import os
import subprocess

import shutil

# 强制 UTF-8 输出（exe 打包环境下控制台可能为 GBK）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 自动使用虚拟环境（仅在非 PyInstaller 打包环境中生效）
if not getattr(sys, 'frozen', False):
    _SCRIPT_DIR = Path(__file__).resolve().parent
    _VENV_PYTHON = _SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
    if _VENV_PYTHON.exists():
        _VENV_PYTHON = _VENV_PYTHON.resolve()
        current = Path(sys.executable).resolve() if sys.executable else None
        if current and str(current).lower() != str(_VENV_PYTHON).lower():
            python_exe = str(_VENV_PYTHON)
            if "pythonw.exe" in current.name:
                python_exe = str(_SCRIPT_DIR / ".venv" / "Scripts" / "pythonw.exe")
            sys.exit(subprocess.call([python_exe] + sys.argv, cwd=_SCRIPT_DIR, env={**os.environ, "PYTHONIOENCODING": "utf-8"}))

def show_help():
    """显示帮助信息"""
    print("""
角色工作流管理器 - 使用说明

**角色卡制作**
  python character_workflow.py auto        - [推荐] 一键全自动制卡 (清理并完整运行)
  python character_workflow.py full        - 执行完整流程 (不清理)
  python character_workflow.py split       - 分割小说文本为文本块
  python character_workflow.py extract     - 从文本块提取角色信息
  python character_workflow.py merge       - 合并重复的角色数据
  python character_workflow.py filter      - 筛选角色，保留前50个最大的文件
  python character_workflow.py create      - 从合并后的数据创建角色卡

**世界书制作**
  python character_workflow.py wb-auto      - [推荐] 一键全自动生成世界书 (清理并完整运行)
  python character_workflow.py wb-extract   - [步骤1] 提取世界书原始条目
  python character_workflow.py wb-generate  - [步骤2] 将原始条目升华为结构化世界书

**通用命令**
  python character_workflow.py status      - 显示工作流状态
  python character_workflow.py clean       - 清理所有中间及输出文件
  python character_workflow.py help        - 显示此帮助信息
""")

def show_status():
    """显示工作流状态"""
    print("="*60)
    print("角色工作流状态")
    print("="*60)
    
    # 检查各个目录的状态
    directories = {
        "文本分块 (chunks)": Path("chunks"),
        "原始角色数据 (character_responses)": Path("character_responses"),
        "合并角色数据 (roles_json)": Path("roles_json"),
        "角色卡 (cards)": Path("cards")
    }
    
    for desc, dir_path in directories.items():
        if dir_path.exists():
            if desc.startswith("文本分块"):
                files = list(dir_path.glob("chunk_*.txt"))
            else:
                files = list(dir_path.glob("*.json"))
                # 排除统计文件
                files = [f for f in files if f.name not in ['character_stats.json']]
            
            print(f"{desc}: {len(files)} 个文件")
            
            # 显示最新文件的时间
            if files:
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                mtime = time.ctime(latest_file.stat().st_mtime)
                print(f"  最新文件: {latest_file.name} ({mtime})")
        else:
            print(f"{desc}: 目录不存在")
    
    # 检查工作流完成度
    print(f"\n工作流完成度:")

    novel_exist = Path("a.txt").exists()
    chunks_exist = Path("chunks").exists() and list(Path("chunks").glob("chunk_*.txt"))
    extracted_exist = Path("character_responses").exists() and list(Path("character_responses").glob("*.json"))
    merged_exist = Path("roles_json").exists() and list(Path("roles_json").glob("*.json"))
    cards_exist = Path("cards").exists() and list(Path("cards").glob("*.json"))

    steps = [
        ("0. 小说文件", novel_exist),
        ("1. 文本分块", chunks_exist),
        ("2. 角色提取", extracted_exist),
        ("3. 角色合并", merged_exist),
        ("4. 角色卡生成", cards_exist)
    ]

    for step_name, completed in steps:
        status = "[完成]" if completed else "[未完成]"
        print(f"  {step_name}: {status}")

    # 推荐下一步操作
    print(f"\n推荐操作:")
    if not novel_exist:
        print("  需要先准备小说文件 a.txt")
    elif not chunks_exist:
        print("  运行: python character_workflow.py split")
    elif not extracted_exist:
        print("  运行: python character_workflow.py extract")
    elif not merged_exist:
        print("  运行: python character_workflow.py merge")
    elif not cards_exist:
        print("  运行: python character_workflow.py create")
    else:
        print("  工作流已完成！可以使用生成的角色卡")

def split_text():
    """分割文本"""
    print("开始文本分割...")
    try:
        from text_splitter import TextSplitter
        from project_config import get_config

        # 从配置文件读取源文件路径
        config = get_config()
        input_file = config.get('input.source_file', 'a.txt')
        if not Path(input_file).exists():
            print(f"错误: 找不到输入文件 {input_file}")
            print("请在 config.yaml 的 input.source_file 中配置正确的小说文件路径")
            return False

        splitter = TextSplitter()
        splitter.split_novel(input_file, "size")
        print("文本分割完成！")
        return True
    except Exception as e:
        print(f"文本分割失败: {e}")
        return False

def extract_characters():
    """提取角色信息"""
    print("开始角色提取...")
    try:
        import asyncio
        from character_extractor_llm import LLMCharacterExtractor
        extractor = LLMCharacterExtractor()
        asyncio.run(extractor.extract_all_characters())
        print("角色提取完成！")
        return True
    except Exception as e:
        print(f"角色提取失败: {e}")
        return False

def merge_characters():
    """合并角色数据"""
    print("开始角色合并...")
    try:
        from character_merger import CharacterMerger
        merger = CharacterMerger()
        merger.merge_all_characters()
        print("角色合并完成！")
        return True
    except Exception as e:
        print(f"角色合并失败: {e}")
        return False

def create_character_cards():
    """创建角色卡"""
    print("开始创建角色卡...")
    try:
        import asyncio
        from create_card import CardCreator
        creator = CardCreator()
        asyncio.run(creator.create_all_cards_async())
        print("角色卡创建完成！")
        return True
    except Exception as e:
        print(f"角色卡创建失败: {e}")
        return False

def filter_characters():
    """筛选角色，保留前50个最大的文件"""
    print("开始筛选角色...")
    try:
        from character_filter import CharacterFilter
        filter_tool = CharacterFilter()

        # 显示统计信息
        filter_tool.show_statistics()

        # 执行筛选
        kept, removed = filter_tool.filter_characters(dry_run=False)

        if removed > 0:
            print(f"[SUCCESS] 角色筛选完成！保留了 {kept} 个最大的角色文件，移除了 {removed} 个较小的文件")
        else:
            print(f"[SUCCESS] 角色筛选完成！当前只有 {kept} 个角色文件，无需筛选")

        return True
    except Exception as e:
        print(f"角色筛选失败: {e}")
        return False

def extract_worldbook():
    """提取世界书条目"""
    print("开始提取世界书原始条目...")
    try:
        import asyncio
        from worldbook_extractor import WorldbookExtractor
        extractor = WorldbookExtractor()
        asyncio.run(extractor.extract_all())
        print("世界书条目提取完成！")
        return True
    except Exception as e:
        print(f"世界书条目提取失败: {e}")
        return False

def classify_worldbook():
    """分类世界书数据"""
    print("开始分类世界书数据...")
    try:
        from worldbook_classifier import WorldbookClassifier
        classifier = WorldbookClassifier()
        success = classifier.classify_all()

        if success:
            print("✅ 世界书数据分类完成")
            return True
        else:
            print("❌ 世界书数据分类失败")
            return False
    except Exception as e:
        print(f"❌ 世界书数据分类过程出错: {e}")
        return False

def generate_worldbook():
    """生成结构化世界书"""
    print("开始生成结构化世界书...")

    # 确保先完成分类
    from pathlib import Path
    classified_dir = Path("wb_responses/classified")
    if not classified_dir.exists() or not any(classified_dir.glob("classified_*.json")):
        print("⚠️ 未找到分类数据，先执行分类步骤...")
        if not classify_worldbook():
            print("❌ 分类步骤失败，无法继续生成")
            return False

    try:
        import asyncio
        from worldbook_generator import WorldbookGenerator
        from project_config import get_config

        generator = WorldbookGenerator()
        config = get_config()

        # 检查启用的架构模式
        event_mode = config.get('event_driven_architecture.enable', True)
        rules_mode = config.get('world_rules.enable_extraction', True)

        if event_mode and rules_mode:
            print("🏗️ 使用三层架构模式生成世界书（规则层+时间线层+事件层）...")
            # 三层架构模式：需要实现完整的三层生成流程
            try:
                async def generate_layered():
                    # 1. 加载分类后的规则数据
                    classified_rules = generator.load_classified_rules()
                    if classified_rules:
                        rule_summaries = await generator.summarize_classified_rules(classified_rules)
                    else:
                        rule_summaries = {}

                    # 2. 加载分类后的事件数据并生成时间线
                    classified_events = generator.load_classified_events()
                    if classified_events:
                        timeline_content = await generator.summarize_timeline_from_classified(classified_events)
                    else:
                        timeline_content = "## 故事时间线\n\n*暂无事件数据*"

                    # 3. 加载分类后的实体数据
                    classified_entities = generator.load_classified_entities()
                    if classified_entities:
                        entity_summaries = await generator.summarize_classified_entities(classified_entities)
                    else:
                        entity_summaries = {}

                    # 4. 生成三层世界书
                    output_file = generator.save_layered_worldbook(
                        rule_summaries, timeline_content, entity_summaries, []  # 暂时不处理事件条目
                    )
                    print(f"✅ 三层架构世界书生成完成: {output_file}")
                    return output_file

                asyncio.run(generate_layered())

            except Exception as e:
                print(f"❌ 三层架构模式失败，回退到事件驱动模式: {e}")
                asyncio.run(generator.generate_timeline_worldbook())

        elif event_mode:
            print("🚀 使用事件驱动模式生成世界书...")
            asyncio.run(generator.generate_timeline_worldbook())
        else:
            print("📚 使用传统模式生成世界书...")
            asyncio.run(generator.generate_worldbook())

        print("结构化世界书生成完成！")

        # 自动转换为SillyTavern V2格式
        print("\n开始转换为SillyTavern V2格式...")
        if convert_worldbook_format():
            print("世界书格式转换完成！")
        else:
            print("世界书格式转换失败，但原始世界书已生成")

        return True
    except Exception as e:
        print(f"结构化世界书生成失败: {e}")
        return False

def convert_worldbook_format():
    """转换世界书为SillyTavern V2格式"""
    try:
        from pathlib import Path
        from code import WorldbookFormatter

        worldbook_dir = Path("worldbook")

        # 检查可能的输入文件
        possible_files = [
            "layered_worldbook.json",  # 三层架构模式
            "timeline_worldbook.json",  # 事件驱动模式
            "worldbook.json"  # 传统模式
        ]

        input_file = None
        for filename in possible_files:
            file_path = worldbook_dir / filename
            if file_path.exists():
                input_file = filename
                print(f"找到世界书文件: {filename}")
                break

        if not input_file:
            print("未找到任何世界书文件进行转换")
            return False

        # 临时复制文件为标准名称以供转换器使用
        source_file = worldbook_dir / input_file
        target_file = worldbook_dir / "worldbook.json"

        if input_file != "worldbook.json":
            import shutil
            shutil.copy2(source_file, target_file)
            print(f"临时复制 {input_file} 为 worldbook.json")

        # 执行转换
        formatter = WorldbookFormatter("worldbook")
        formatter.convert()

        # 清理临时文件
        if input_file != "worldbook.json" and target_file.exists():
            target_file.unlink()
            print("清理临时文件")

        return True
    except Exception as e:
        print(f"世界书格式转换失败: {e}")
        return False

def clean_worldbook_files():
    """清理世界书相关的文件和目录"""
    print("清理世界书相关目录...")
    dirs_to_clean = [
        Path("chunks"),           # 添加chunks目录清理
        Path("wb_responses"),
        Path("wb_raw_responses"),
        Path("wb_bad_chunks"),
        Path("worldbook")
    ]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"已删除目录: {dir_path}")
            except Exception as e:
                print(f"删除目录失败 {dir_path}: {e}")
    print("世界书目录清理完成！")

def run_wb_auto_workflow():
    """运行一键全自动世界书生成流程"""
    print("="*60)
    print("开始执行一键全自动世界书生成流程")
    print("="*60)

    # 步骤0: 清理世界书相关目录
    print("\n步骤0: 清理世界书相关目录")
    clean_worldbook_files()

    # 步骤1: 分割文本（强制重新分割）
    print("\n步骤1: 分割小说文本")
    if not split_text():
        print("工作流中断：文本分割失败")
        return

    # 步骤2: 提取世界书条目
    print("\n步骤2: 提取世界书原始条目")
    if not extract_worldbook():
        print("工作流中断：世界书提取失败")
        return

    # 步骤3: 生成结构化世界书
    print("\n步骤3: 生成结构化世界书")
    if not generate_worldbook():
        print("工作流中断：世界书生成失败")
        return

    print("\n="*60)
    print("世界书工作流执行成功！")
    print("="*60)

    # 显示最终统计
    show_wb_final_stats()

def show_wb_final_stats():
    """显示世界书最终统计信息"""
    print("\n世界书统计:")

    # 统计各阶段的文件数量
    chunks_count = len(list(Path("chunks").glob("chunk_*.txt"))) if Path("chunks").exists() else 0
    wb_extracted_count = len(list(Path("wb_responses").glob("*.json"))) if Path("wb_responses").exists() else 0
    worldbook_files = len(list(Path("worldbook").glob("*.json"))) if Path("worldbook").exists() else 0

    print(f"  文本分块: {chunks_count} 个")
    print(f"  提取条目: {wb_extracted_count} 个文件")
    print(f"  生成世界书: {worldbook_files} 个文件")

    # 统计总条目数
    total_entries = 0
    if Path("wb_responses").exists():
        for wb_file in Path("wb_responses").glob("*.json"):
            try:
                with open(wb_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    if isinstance(data, list):
                        total_entries += len(data)
            except:
                pass

    print(f"  总提取条目: {total_entries} 个")

    if Path("worldbook").exists():
        print(f"  输出位置: worldbook/ 目录")

def run_auto_workflow():
    """运行一键全自动工作流"""
    print("="*60)
    print("开始执行一键全自动制卡流程")
    print("="*60)

    # 步骤0: 清理
    print("\n步骤0: 清理旧文件和目录")
    clean_all()

    # 运行完整工作流
    run_full_workflow()

def clean_all():
    """清理所有生成的文件和目录"""
    print("清理所有中间目录和输出目录...")
    dirs_to_clean = [
        Path("chunks"),
        Path("character_responses"),
        Path("character_responses_bad"),
        Path("character_responses_raw"),
        Path("roles_json"),
        Path("cards"),
        Path("wb_responses"),
        Path("worldbook"),
    ]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"已删除目录: {dir_path}")
            except Exception as e:
                print(f"删除目录失败 {dir_path}: {e}")
    print("清理完成！")

def run_full_workflow():
    """运行完整工作流"""
    print("="*60)
    print("开始执行完整角色工作流")
    print("="*60)

    # 步骤0: 分割文本
    print("\n步骤0: 分割小说文本")
    if not split_text():
        print("工作流中断：文本分割失败")
        return False

    # 步骤1: 提取角色
    print("\n步骤1: 从文本块提取角色信息")
    if not extract_characters():
        print("工作流中断：角色提取失败")
        return False

    # 步骤2: 合并角色
    print("\n步骤2: 合并重复角色数据")
    if not merge_characters():
        print("工作流中断：角色合并失败")
        return False

    # 步骤3: 筛选角色
    print("\n步骤3: 筛选角色，保留前50个最大的文件")
    if not filter_characters():
        print("工作流中断：角色筛选失败")
        return False

    # 步骤4: 创建角色卡
    print("\n步骤4: 生成角色卡")
    if not create_character_cards():
        print("工作流中断：角色卡创建失败")
        return False

    print("\n="*60)
    print("完整角色工作流执行成功！")
    print("="*60)

    # 显示最终统计
    show_final_stats()
    return True

def show_final_stats():
    """显示最终统计信息"""
    print("\n最终统计:")
    
    # 统计各阶段的文件数量
    chunks_count = len(list(Path("chunks").glob("chunk_*.txt"))) if Path("chunks").exists() else 0
    extracted_count = len(list(Path("character_responses").glob("*.json"))) if Path("character_responses").exists() else 0
    merged_count = len([f for f in Path("roles_json").glob("*.json") if f.name != "character_stats.json"]) if Path("roles_json").exists() else 0
    cards_count = len(list(Path("cards").glob("*.json"))) if Path("cards").exists() else 0
    
    print(f"  文本分块: {chunks_count} 个")
    print(f"  提取角色: {extracted_count} 个")
    print(f"  合并角色: {merged_count} 个")
    print(f"  角色卡: {cards_count} 个")
    
    # 计算处理效率
    if chunks_count > 0 and merged_count > 0:
        efficiency = merged_count / chunks_count
        print(f"  处理效率: 每个文本块平均提取 {efficiency:.2f} 个角色")

def clean_intermediate_files():
    """清理中间文件"""
    print("清理中间文件...")
    
    # 清理character_responses目录
    responses_dir = Path("character_responses")
    if responses_dir.exists():
        for file in responses_dir.glob("*.json"):
            file.unlink()
            print(f"删除: {file}")
        
        # 如果目录为空，删除目录
        try:
            responses_dir.rmdir()
            print(f"删除目录: {responses_dir}")
        except:
            pass
    
    print("中间文件清理完成！")

def run_workflow_mode(mode: str) -> bool:
    """
    按名称运行工作流模式。可被外部代码直接调用（导入）。

    Args:
        mode: 工作流模式名（auto, full, split, extract, merge, filter, create,
              wb-auto, wb-extract, wb-generate, status, clean, help 等）

    Returns:
        True 表示成功，False 表示失败或未知模式
    """
    mode = mode.lower()

    if mode == "auto":
        run_auto_workflow()
        return True
    elif mode == "split":
        return split_text()
    elif mode == "extract":
        return extract_characters()
    elif mode == "merge":
        return merge_characters()
    elif mode == "filter":
        return filter_characters()
    elif mode == "full":
        return run_full_workflow()
    elif mode == "create":
        return create_character_cards()
    elif mode == "wb-extract":
        return extract_worldbook()
    elif mode == "wb-classify":
        return classify_worldbook()
    elif mode == "wb-generate":
        return generate_worldbook()
    elif mode == "wb-auto":
        run_wb_auto_workflow()
        return True
    elif mode == "status":
        show_status()
        return True
    elif mode == "clean":
        clean_all()
        return True
    elif mode == "help":
        show_help()
        return True
    else:
        print(f"未知命令: {mode}")
        show_help()
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()
    run_workflow_mode(command)


if __name__ == "__main__":
    main()
