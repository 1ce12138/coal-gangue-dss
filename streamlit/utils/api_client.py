"""
API 客户端 — 对接 MiniMax 技术经济评估服务。
"""

import json
import random
import re
import time

import streamlit as st


class EvalAPIClient:
    """评估 API 客户端（支持 Demo / 真实 MiniMax 两种模式）"""

    def __init__(self, config: dict):
        self.base_url = config.get("base_url", "")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "MiniMax-M2.7")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.3)
        self.is_demo = not bool(self.api_key)

    def evaluate(self, scheme_text: str, rag_context: str = "") -> dict:
        if self.is_demo:
            return self._demo_evaluate(scheme_text)
        return self._real_evaluate(scheme_text, rag_context)

    def _real_evaluate(self, scheme_text: str, rag_context: str = "") -> dict:
        try:
            import requests

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self._build_system_prompt(rag_context)},
                    {"role": "user", "content": f"请对以下煤矸石资源化利用方案进行技术经济决策评估：\n\n{scheme_text}"},
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_response(content)
        except Exception as e:
            st.error(f"API 调用失败: {str(e)}")
            return self._demo_evaluate(scheme_text)

    def _demo_evaluate(self, scheme_text: str) -> dict:
        time.sleep(random.uniform(0.4, 1.0))
        seed = sum(ord(c) for c in scheme_text[:80]) % 100
        random.seed(seed)
        tech_score = random.uniform(60, 95)
        econ_score = random.uniform(55, 92)
        risk_score = random.uniform(58, 96)
        overall = tech_score * 0.45 + econ_score * 0.45 + risk_score * 0.10
        return {
            "scores": {
                "技术可行性": round(tech_score, 1),
                "经济可行性": round(econ_score, 1),
                "实施风险与约束": round(risk_score, 1),
            },
            "overall_score": round(overall, 1),
            "reasoning": {
                "技术可行性": self._generate_demo_reasoning("技术可行性", tech_score),
                "经济可行性": self._generate_demo_reasoning("经济可行性", econ_score),
                "实施风险与约束": self._generate_demo_reasoning("实施风险与约束", risk_score),
            },
            "overall_comment": (
                f"该方案综合评分为 {overall:.1f} 分。"
                f"技术可行性{'表现优异' if tech_score > 80 else '存在一定优化空间'}，"
                f"经济可行性{'较为突出' if econ_score > 80 else '需进一步论证'}，"
                f"实施风险与约束{'整体可控' if risk_score > 80 else '仍需重点识别'}。"
                f"建议{'优先进入详细可研阶段' if overall > 80 else '补充技术经济参数后再推进'}。"
            ),
            "rag_references": [],
        }

    def _generate_demo_reasoning(self, dimension: str, score: float) -> str:
        level = "优秀" if score >= 85 else "良好" if score >= 70 else "一般"
        templates = {
            "技术可行性": {
                "优秀": "技术路线成熟可靠，设备条件明确，工艺流程完整，具备工程化应用基础。",
                "良好": "技术路线基本可行，主要工艺环节已有案例，但仍需补充中试或工程参数。",
                "一般": "技术成熟度和工程放大条件仍不充分，需要进一步论证。",
            },
            "经济可行性": {
                "优秀": "投入产出关系清晰，产品消纳能力较强，具备较好的投资吸引力。",
                "良好": "经济可行性较好，但仍需进一步核算成本、价格和消纳规模。",
                "一般": "投资、运营成本或收益来源存在不确定性，需要补充敏感性分析。",
            },
            "实施风险与约束": {
                "优秀": "环保合规、政策适配和市场风险整体可控。",
                "良好": "存在一般实施约束，可通过工程和管理措施进一步降低风险。",
                "一般": "环保、市场或组织实施约束较明显，需要专项风险识别。",
            },
        }
        return templates.get(dimension, {}).get(level, "评估数据不足，建议补充更多信息。")

    def _build_system_prompt(self, rag_context: str = "") -> str:
        prompt = """你是一位煤矸石资源化利用领域的技术经济评价专家，具备环境工程、化学工程、技术经济学与管理科学的跨学科背景。

请严格按照以下技术经济决策评估框架，对方案进行保守、可解释的评分。信息不足时，应在理由中说明不确定性。

评估维度与权重：
1. 技术可行性（45%）：工艺技术成熟度、设备可获取性、技术风险等级、产品质量达标率。
2. 经济可行性（45%）：初始投资规模、运营成本、投资回收期、市场需求量、产品价格或收益来源。
3. 实施风险与约束（10%）：环保合规约束、政策适配、市场与供应链风险、工程实施复杂度。

请不要输出思考过程、Markdown 或额外解释，只严格输出以下 JSON 对象：
{
  "scores": {"技术可行性": 分数, "经济可行性": 分数, "实施风险与约束": 分数},
  "reasoning": {"技术可行性": "评分理由", "经济可行性": "评分理由", "实施风险与约束": "评分理由"},
  "overall_comment": "综合评价与建议"
}"""
        if rag_context:
            prompt += f"\n\n参考文献知识库检索结果：\n{rag_context}"
        return prompt

    def _parse_response(self, content: str) -> dict:
        clean_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        try:
            start = clean_content.find("{")
            end = clean_content.rfind("}") + 1
            data = json.loads(clean_content[start:end]) if start >= 0 and end > start else {}
            scores = self._normalize_scores(data.get("scores", {}))
            overall = scores["技术可行性"] * 0.45 + scores["经济可行性"] * 0.45 + scores["实施风险与约束"] * 0.10
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
        except Exception:
            return {
                "scores": {"技术可行性": 0, "经济可行性": 0, "实施风险与约束": 0},
                "overall_score": 0,
                "reasoning": {"技术可行性": "模型返回内容未能解析为标准 JSON。", "经济可行性": "", "实施风险与约束": ""},
                "overall_comment": "评估结果解析失败，请检查 API 返回格式。",
                "rag_references": [],
            }

    def _normalize_scores(self, scores: dict) -> dict:
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
        if self.is_demo:
            return {"status": "demo", "message": "当前为演示模式（未配置 API Key）"}
        try:
            import requests
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 8},
                timeout=10,
            )
            return {"status": "connected", "message": "API 连接成功"} if resp.status_code == 200 else {"status": "error", "message": f"API 返回状态码 {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}
