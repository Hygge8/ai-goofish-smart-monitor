import json
import os
import sys
from typing import Awaitable, Callable, Optional

import aiofiles

from src.infrastructure.external.ai_client import AIClient

# 默认参考模板：当 prompts/macbook_criteria.txt 不存在时自动创建，避免首次部署创建 AI 任务失败。
DEFAULT_REFERENCE_CRITERIA_TEXT = """
# 闲鱼商品 AI 分析标准参考模板

[V6.3 核心升级] 你是一个二手商品筛选助手，目标是在闲鱼商品中筛出值得进一步联系的优质商品，并过滤风险较高、信息不足或疑似套路的商品。

## 一、总体判断原则

1. 优先推荐：真实个人卖家、描述完整、图片清晰、价格合理、支持平台交易、沟通风险低的商品。
2. 谨慎推荐：价格略低但信息不足、图片较少、卖家描述含糊、发布时间过久或存在轻微疑点的商品。
3. 不推荐：明显商家批量号、引流到站外、价格异常低、要求微信/QQ/支付宝/线下交易、描述与图片不符、疑似翻新/维修/问题商品。

## 二、一票否决硬性原则

只要命中以下任一情况，直接判定为不推荐：

- 要求脱离平台交易，例如加微信、QQ、支付宝、银行卡、线下交易。
- 标题或描述中出现明显骗局、引流、代拍、定金、到付、先款等高风险信息。
- 商品价格显著低于正常市场价，且没有合理解释。
- 卖家描述刻意回避关键问题，例如成色、维修、故障、来源、配件。
- 图片疑似网图、盗图、过度美化，或图片与标题描述明显不一致。
- 商品存在明确故障、锁机、账号锁、进水、维修严重、无法正常使用等情况。

## 三、重点分析维度

### 1. 商品真实性

- 图片是否为实拍。
- 图片数量是否足够。
- 标题、描述、图片是否一致。
- 是否展示关键细节，例如外观、配件、型号、使用痕迹。

### 2. 价格合理性

- 与同类商品市场价格相比是否合理。
- 价格过低时必须提高风险判断。
- 价格合理且描述完整，可提高推荐倾向。

### 3. 卖家可信度

- 是否像个人闲置卖家。
- 是否存在大量同类商品、批量售卖、回收、商家话术。
- 是否愿意平台内沟通与交易。

### 4. 描述完整度

- 是否说明购买时间、使用情况、成色、配件、维修记录、出售原因。
- 描述越完整，可信度越高。
- 描述过短、只写“懂的来”“不议价”“捡漏”等，需要谨慎。

## 四、危险信号清单

出现以下内容时应降低推荐：

- “秒出”“捡漏”“急出”“不刀”“到付”“定金”“先款”。
- “微信详聊”“QQ 联系”“支付宝转账”“线下交易”。
- “维修过”“进水”“换过主板”“账号锁”“密码忘了”。
- 图片极少、模糊、无实物图、只有官网图或宣传图。
- 卖家同一账号发布大量相似商品。

## 五、输出要求

请根据商品信息给出清晰判断，输出内容需要包含：

- 是否推荐。
- 推荐或不推荐的核心理由。
- 主要风险点。
- 可以继续询问卖家的问题。

判断要简洁、直接、可解释，不要只给空泛结论。
""".strip()

# The meta-prompt to instruct the AI
META_PROMPT_TEMPLATE = """
你是一位世界级的AI提示词工程大师。你的任务是根据用户提供的【购买需求】，模仿一个【参考范例】，为闲鱼监控机器人的AI分析模块（代号 EagleEye）生成一份全新的【分析标准】文本。

你的输出必须严格遵循【参考范例】的结构、语气和核心原则，但内容要完全针对用户的【购买需求】进行定制。最终生成的文本将作为AI分析模块的思考指南。

---
这是【参考范例】（`macbook_criteria.txt`）：
```text
{reference_text}
```
---

这是用户的【购买需求】：
```text
{user_description}
```
---

请现在开始生成全新的【分析标准】文本。请注意：
1.  **只输出新生成的文本内容**，不要包含任何额外的解释、标题或代码块标记。
2.  保留范例中的 `[V6.3 核心升级]`、`[V6.4 逻辑修正]` 等版本标记，这有助于保持格式一致性。
3.  将范例中所有与 "MacBook" 相关的内容，替换为与用户需求商品相关的内容。
4.  思考并生成针对新商品类型的“一票否决硬性原则”和“危险信号清单”。
"""

ProgressCallback = Callable[[str, str], Awaitable[None]]


async def _report_progress(
    progress_callback: Optional[ProgressCallback],
    step_key: str,
    message: str,
) -> None:
    if progress_callback:
        await progress_callback(step_key, message)


def _ensure_default_reference_file(reference_file_path: str) -> str:
    """首次部署时自动生成默认参考模板。"""
    directory = os.path.dirname(reference_file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(reference_file_path, "w", encoding="utf-8") as file:
        file.write(DEFAULT_REFERENCE_CRITERIA_TEXT)
    return DEFAULT_REFERENCE_CRITERIA_TEXT


def _read_reference_text(reference_file_path: str) -> str:
    try:
        with open(reference_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if content:
                return content
            return _ensure_default_reference_file(reference_file_path)
    except FileNotFoundError:
        print(f"参考文件不存在，已自动创建默认模板: {reference_file_path}")
        return _ensure_default_reference_file(reference_file_path)
    except IOError as exc:
        raise IOError(f"读取参考文件失败: {exc}")


async def _request_generated_text(ai_client: AIClient, prompt: str) -> str:
    print("正在调用AI生成新的分析标准，请稍候...")
    try:
        generated_text = await ai_client._call_ai(
            [{"role": "user", "content": prompt}],
            temperature=0.5,
            max_output_tokens=800,
            enable_json_output=False,
        )
    except Exception as exc:
        print(f"调用 OpenAI API 时出错: {exc}")
        raise

    print("AI已成功生成内容。")
    return generated_text.strip()


async def _close_ai_client(
    ai_client: AIClient,
    active_error: BaseException | None,
) -> None:
    try:
        await ai_client.close()
    except Exception as close_error:
        print(f"关闭 AI 客户端时出错: {close_error}")
        if active_error is None:
            raise


async def generate_criteria(
    user_description: str,
    reference_file_path: str,
    progress_callback: Optional[ProgressCallback] = None,
) -> str:
    """
    Generates a new criteria file content using AI.
    """
    ai_client = AIClient()
    active_error: BaseException | None = None
    try:
        if not ai_client.is_available():
            ai_client.refresh()
        if not ai_client.is_available():
            raise RuntimeError("AI客户端未初始化，无法生成分析标准。请检查.env配置。")

        await _report_progress(progress_callback, "reference", "正在读取参考文件。")
        print(f"正在读取参考文件: {reference_file_path}")
        reference_text = _read_reference_text(reference_file_path)

        await _report_progress(progress_callback, "prompt", "正在构建发送给 AI 的指令。")
        print("正在构建发送给AI的指令...")
        prompt = META_PROMPT_TEMPLATE.format(
            reference_text=reference_text,
            user_description=user_description,
        )

        await _report_progress(progress_callback, "llm", "正在调用 AI 生成分析标准。")
        return await _request_generated_text(ai_client, prompt)
    except Exception as exc:
        active_error = exc
        raise
    finally:
        await _close_ai_client(ai_client, active_error)


async def update_config_with_new_task(new_task: dict, config_file: str = "config.json"):
    """
    将一个新任务添加到指定的JSON配置文件中。
    """
    print(f"正在更新配置文件: {config_file}")
    try:
        # 读取现有配置
        config_data = []
        if os.path.exists(config_file):
            async with aiofiles.open(config_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                # 处理空文件的情况
                if content.strip():
                    try:
                        config_data = json.loads(content)
                        print(f"成功读取现有配置，当前任务数量: {len(config_data)}")
                    except json.JSONDecodeError as e:
                        print(f"解析配置文件失败，将创建新配置: {e}")
                        config_data = []
        else:
            print(f"配置文件不存在，将创建新文件: {config_file}")

        # 追加新任务
        config_data.append(new_task)

        # 写回配置文件
        async with aiofiles.open(config_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(config_data, ensure_ascii=False, indent=2))
            print(f"配置文件写入完成")

        print(f"成功！新任务 '{new_task.get('task_name')}' 已添加到 {config_file} 并已启用。")
        return True
    except json.JSONDecodeError as e:
        error_msg = f"错误: 配置文件 {config_file} 格式错误，无法解析: {e}"
        sys.stderr.write(error_msg + "\n")
        print(error_msg)
        return False
    except IOError as e:
        error_msg = f"错误: 读写配置文件失败: {e}"
        sys.stderr.write(error_msg + "\n")
        print(error_msg)
        return False
    except Exception as e:
        error_msg = f"错误: 更新配置文件时发生未知错误: {e}"
        sys.stderr.write(error_msg + "\n")
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return False
