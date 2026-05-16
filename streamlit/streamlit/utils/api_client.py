"""
API 客户端 — 对接 MiniMax / OpenClaw 评估服务
当前为 Demo 模式（使用模拟数据），待 API 配置后可无缝切换为真实调用。
"""

import json
import re
import time
import random
import streamlit as st
from typing import Optional


class EvalAPIClient:
    """评估 API 客户端（支持 Demo / 真实 两种模式）"""

    def __init__(self, config: dict):
        self.base_url = config.get("base_url", "")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "MiniMax-Text-01")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.3)
        self.is_demo = not bool(self.api_key)

    def evaluate(self, scheme_text: str, rag_context: str = "") -> dict:
        """
        对单个方案进行多维度评估。
        Returns:
            dict: {
                "scores": {"技术可行性": float, "经济可行性": float, "实施风险与约束": float},
                "overall_score": float,
                "reasoning": {"技术可行性": str, "经济可行性": str, "实施风险与约束": str},
                "overall_comment": str,
                "rag_references": list[str],
            }
        """
        if self.is_demo:
            return self._demo_evaluate(scheme_text)
        else:
            return self._real_evaluate(scheme_text, rag_context)

    def _real_evaluate(self, scheme_text: str, rag_context: str = "") -> dict:
        """真实 API 调用（需要配置 API Key 后启用）"""
        try:
            import requests

            system_prompt = self._build_system_prompt(rag_context)

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请对以下煤矸石资源化利用方案进行技术经济决策评估：\n\n{scheme_text}"},
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return self._parse_response(content)

        except Exception as e:
            st.error(f"API 调用失败: {str(e)}")
            return self._demo_evaluate(scheme_text)

    def _demo_evaluate(self, scheme_text: str) -> dict:
        """Demo 模式 — 生成模拟评估结果"""
        # 模拟 API 延迟
        time.sleep(random.uniform(0.5, 1.5))

        # 根据方案内容生成有差异的合理分数
        seed = sum(ord(c) for c in scheme_text[:50]) % 100
        random.seed(seed)

        tech_score = random.uniform(60, 95)
        econ_score = random.uniform(55, 92)
        risk_score = random.uniform(58, 96)

        # 加权综合分
        overall = tech_score * 0.45 + econ_score * 0.45 + risk_score * 0.10

        reasoning = {
            "技术可行性": self._generate_demo_reasoning("技术可行性", tech_score),
            "经济可行性": self._generate_demo_reasoning("经济可行性", econ_score),
            "实施风险与约束": self._generate_demo_reasoning("实施风险与约束", risk_score),
        }

        rag_refs = [
            "张伟等. 煤矸石资源化利用技术研究进展[J]. 矿业研究与开发, 2023.",
            "李明. 煤矸石综合利用经济效益分析[J]. 煤炭经济研究, 2022.",
            "王芳等. 煤矸石处置的环境影响评价方法研究[J]. 环境科学与技术, 2023.",
        ]

        return {
            "scores": {
                "技术可行性": round(tech_score, 1),
                "经济可行性": round(econ_score, 1),
                "实施风险与约束": round(risk_score, 1),
            },
            "overall_score": round(overall, 1),
            "reasoning": reasoning,
            "overall_comment": (
                f"该方案综合评分为 {overall:.1f} 分。"
                f"技术可行性{'表现优异' if tech_score > 80 else '存在一定优化空间'}，"
                f"经济可行性{'较为突出' if econ_score > 80 else '需进一步论证'}，"
                f"实施风险与约束{'整体可控' if risk_score > 80 else '仍需重点识别'}。"
                f"建议{'优先进入详细可研阶段' if overall > 80 else '补充技术经济参数后再推进'}。"
            ),
            "rag_references": rag_refs,
        }

    def _generate_demo_reasoning(self, dimension: str, score: float) -> str:
        """生成模拟评估理由"""
        level = "优秀" if score >= 85 else "良好" if score >= 70 else "一般"

        templates = {
            "技术可行性": {
                "优秀": "该方案采用的技术路线成熟可靠，设备选型合理，工艺流程完整，产品质量可控。技术风险较低，具备大规模工业化应用条件。",
                "良好": "该方案技术路线基本可行，主要工艺环节已有成功案例。部分设备需要定制化改造，建议加强中试验证。",
                "一般": "该方案技术路线仍处于实验室或中试阶段，工业化放大存在不确定性。建议开展进一步的技术论证和试验验证。",
            },
            "经济可行性": {
                "优秀": "该方案投资回收期短，运营成本可控，产品市场需求较强，具备较好的投入产出关系和投资吸引力。",
                "良好": "该方案经济可行性较好，初始投资与运营成本处于可接受区间，但仍需进一步核算产品价格和消纳规模。",
                "一般": "该方案初始投资或运营成本压力较大，投资回收期存在不确定性，需补充成本收益测算和敏感性分析。",
            },
            "实施风险与约束": {
                "优秀": "该方案主要实施约束较少，环保合规、政策适配和市场消纳风险整体可控，具备进入下一阶段论证的条件。",
                "良好": "该方案存在一定工程实施和市场消纳约束，但通过完善环保治理、供应链安排和项目组织可进一步降低风险。",
                "一般": "该方案面临较明显的环保、市场或工程实施约束，需要开展专项风险识别和约束条件校核。",
            },
        }

        return templates.get(dimension, {}).get(level, "评估数据不足，建议补充更多信息。")

    def _build_system_prompt(self, rag_context: str = "") -> str:
        """构建评估用的 System Prompt"""
        base_prompt = """你是一位煤矸石资源化利用领域的技术经济评价专家，具备环境工程、化学工程、技术经济学与管理科学的跨学科背景。

你需要严格按照以下技术经济决策评估框架，对煤矸石资源化利用方案进行评分。评分应保守、可解释，并优先依据用户提供的方案事实；信息不足时应在理由中说明不确定性。

## 评估维度与权重

### 1. 技术可行性（权重 45%）
评分要素：工艺技术成熟度、设备可获取性、技术风险等级、产品质量达标率
- 90-100分：技术成熟，已有大规模工业化应用
- 70-89分：技术基本可行，部分环节需优化
- 60-69分：技术仍在中试阶段
- 60分以下：技术不成熟，风险较高

### 2. 经济可行性（权重 45%）
评分要素：初始投资规模、运营成本、投资回收期、市场需求量、产品价格或收益来源
- 90-100分：投资回收期短，收益显著
- 70-89分：经济可行，收益合理
- 60-69分：投资回收期偏长，收益一般
- 60分以下：经济可行性存疑

### 3. 实施风险与约束（权重 10%）
评分要素：环保合规约束、政策适配、市场与供应链风险、工程实施复杂度
- 90-100分：约束较少，风险高度可控
- 70-89分：存在一般约束，但可通过工程或管理措施控制
- 60-69分：存在较明显约束，需要专项论证
- 60分以下：实施约束突出，近期推进风险较高

## 输出格式

请不要输出思考过程、Markdown 或额外解释，只严格输出以下 JSON 对象：
{
    "scores": {"技术可行性": 分数, "经济可行性": 分数, "实施风险与约束": 分数},
    "reasoning": {"技术可行性": "评分理由", "经济可行性": "评分理由", "实施风险与约束": "评分理由"},
    "overall_comment": "综合评价与建议"
}"""

        if rag_context:
            base_prompt += f"\n\n## 参考文献知识库检索结果\n\n{rag_context}"

        return base_prompt

    def _parse_response(self, content: str) -> dict:
        """解析 LLM 返回的评估结果"""
        clean_content = self._strip_thinking(content)
        try:
            json_text = self._extract_json(clean_content)
            if json_text:
                data = json.loads(json_text)
                scores = self._normalize_scores(data.get("scores", {}))
                overall = (
                    scores.get("技术可行性", 0) * 0.45
                    + scores.get("经济可行性", 0) * 0.45
                    + scores.get("实施风险与约束", 0) * 0.10
                )
                reasoning = data.get("reasoning", {})
                return {
                    "scores": scores,
                    "overall_score": round(overall, 1),
                    "reasoning": {
                        "技术可行性": reasoning.get("技术可行性", ""),
                        "经济可行性": reasoning.get("经济可行性", reasoning.get("经济效益", "")),
                        "实施风险与约束": reasoning.get("实施风险与约束", reasoning.get("环境合规性", "")),
                    },
                    "overall_comment": data.get("overall_comment", ""),
                    "rag_references": [],
                }
        except json.JSONDecodeError:
            pass

        # 解析失败时返回默认结构
        return {
            "scores": {"技术可行性": 0, "经济可行性": 0, "实施风险与约束": 0},
            "overall_score": 0,
            "reasoning": {"技术可行性": "模型返回内容未能解析为标准 JSON。", "经济可行性": "", "实施风险与约束": ""},
            "overall_comment": "评估结果解析失败，请检查 API 返回格式。",
            "rag_references": [],
        }

    def _strip_thinking(self, content: str) -> str:
        """移除部分推理模型可能返回的思考标签。"""
        return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    def _extract_json(self, content: str) -> str:
        """从模型输出中提取第一个完整 JSON 对象。"""
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return content[start:end]
        return ""

    def _normalize_scores(self, scores: dict) -> dict:
        """兼容旧字段名，并将模型输出约束在 0-100 分。"""
        aliases = {
            "技术可行性": ["技术可行性"],
            "经济可行性": ["经济可行性", "经济效益"],
            "实施风险与约束": ["实施风险与约束", "环境合规性"],
        }
        normalized = {}
        for target, candidates in aliases.items():
            value = 0
            for key in candidates:
                if key in scores:
                    value = scores[key]
                    break
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0
            normalized[target] = round(max(0, min(100, value)), 1)
        return normalized

    def check_connection(self) -> dict:
        """检测 API 连接状态"""
        if self.is_demo:
            return {"status": "demo", "message": "当前为演示模式（未配置 API Key）"}
        try:
            import requests
            resp = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                return {"status": "connected", "message": "API 连接成功"}
            else:
                return {"status": "error", "message": f"API 返回状态码 {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}
