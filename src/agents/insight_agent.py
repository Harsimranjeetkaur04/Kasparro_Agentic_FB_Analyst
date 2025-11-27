# src/agents/insight_agent.py

from typing import Dict, Any, List
from agents.agent_base import AgentBase
from utils.logger import log_agent
import math


class InsightAgent(AgentBase):
    """
    Insight Agent:
    - Consumes the data summary produced by DataAgent
    - Produces structured hypotheses explaining performance patterns
    - Each hypothesis includes: id, statement, confidence, evidence, evidence_needed
    - If confidence is low, suggests further queries/aggregation
    """

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            summary = inputs.get("summary") or inputs.get("payload") or {}
            if not summary:
                raise ValueError("Missing summary in inputs")

            log_agent("insight_agent", "Generating hypotheses from summary")

            hypotheses = self._generate_hypotheses(summary)

            # compute average confidence to decide if reflection is needed
            avg_conf = (
                sum(h.get("confidence", 0) for h in hypotheses) / max(1, len(hypotheses))
            )

            result = {
                "status": "ok",
                "payload": {
                    "hypotheses": hypotheses,
                    "avg_confidence": float(avg_conf)
                },
                "confidence": float(avg_conf)
            }

            # If confidence below threshold, include reflection suggestion
            min_conf = float(self.config.get("confidence_min", 0.6))
            if avg_conf < min_conf:
                result["payload"]["action"] = "request_more_data"
                result["payload"]["suggested_queries"] = [
                    {"query": "Provide campaign-level daily CTR for the last 14 days"},
                    {"query": "Breakdown by audience_type and creative_type for low CTR campaigns"}
                ]

            return result

        except Exception as e:
            log_agent("insight_agent", f"ERROR: {str(e)}")
            return {"status": "error", "error": str(e), "confidence": 0.0}

    # ---------------------------
    def _generate_hypotheses(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Heuristic-driven hypothesis generation.
        Uses simple rules over the provided summary.
        """

        hypos: List[Dict[str, Any]] = []
        global_summary = summary.get("global", {})
        trend = summary.get("trend", []) or []
        campaigns = summary.get("campaign_summaries", []) or []
        low_ctr = summary.get("low_ctr_campaigns", []) or summary.get("low_ctr_campaigns", [])

        # --- Hypothesis 1: ROAS trend
        if trend:
            # measure simple slope of ROAS over time (last vs first)
            try:
                if len(trend) >= 2:
                    first_roas = float(trend[0].get("roas", 0) or 0)
                    last_roas = float(trend[-1].get("roas", 0) or 0)
                    if first_roas == 0:
                        roas_change = 0.0
                    else:
                        roas_change = (last_roas - first_roas) / max(abs(first_roas), 1e-9)
                else:
                    roas_change = 0.0
            except Exception:
                roas_change = 0.0

            stmt = "ROAS has decreased over the observed period." if roas_change < 0 else "ROAS is stable or increasing."
            confidence = 0.7 if abs(roas_change) >= 0.05 else 0.45  # simple heuristic

            hypos.append({
                "id": "h_roas_trend",
                "statement": stmt,
                "confidence": float(confidence),
                "evidence": {"first_roas": first_roas if trend else None, "last_roas": last_roas if trend else None, "roas_change": roas_change},
                "evidence_needed": ["statistical_test_on_roas_last_vs_first_period", "per_campaign_roas_trend"]
            })

        # --- Hypothesis 2: CTR drop / creative underperformance
        avg_ctr = float(global_summary.get("avg_ctr", 0.0) or 0.0)
        low_ctr_list = list(set(low_ctr))
        if low_ctr_list:
            stmt = f"Several campaigns show low CTR (bottom 25%): {low_ctr_list[:5]}"
            confidence = 0.75
            hypos.append({
                "id": "h_low_ctr",
                "statement": stmt,
                "confidence": float(confidence),
                "evidence": {"avg_ctr": avg_ctr, "low_ctr_campaigns_sample": low_ctr_list[:5]},
                "evidence_needed": ["per_campaign_creative_messages", "audience_overlap_analysis"]
            })

        # --- Hypothesis 3: Spend vs Conversions mismatch
        try:
            total_spend = float(global_summary.get("total_spend", 0.0) or 0.0)
            total_revenue = float(global_summary.get("total_revenue", 0.0) or 0.0)
            roas = float(global_summary.get("avg_roas", 0.0) or 0.0)
            if total_spend > 0 and total_revenue / (total_spend + 1e-9) < 1.0:
                stmt = "Spend has increased relative to revenue, indicating efficiency loss."
                confidence = 0.6
                hypos.append({
                    "id": "h_spend_efficiency",
                    "statement": stmt,
                    "confidence": float(confidence),
                    "evidence": {"total_spend": total_spend, "total_revenue": total_revenue, "avg_roas": roas},
                    "evidence_needed": ["time_series_spend_vs_revenue", "per_adset_conversion_rates"]
                })
        except Exception:
            pass

        # --- Hypothesis 4: Audience fatigue or frequency issues (heuristic)
        # Look for hint: if multiple campaigns have low CTR and impressions are high
        try:
            fatigues = []
            for c in campaigns:
                ctr = float(c.get("ctr", 0) or 0)
                imps = int(c.get("impressions", 0) or 0)
                if ctr < avg_ctr * 0.7 and imps > 1000:
                    fatigues.append({"campaign": c.get("campaign_name"), "ctr": ctr, "impressions": imps})
            if fatigues:
                hypos.append({
                    "id": "h_audience_fatigue",
                    "statement": "Some campaigns show low CTR despite high impressions, suggesting possible audience fatigue or frequency issues.",
                    "confidence": 0.6,
                    "evidence": {"fatigue_candidates": fatigues[:5]},
                    "evidence_needed": ["frequency_by_audience", "audience_overlap_matrix"]
                })
        except Exception:
            pass

        # If no hypotheses produced, be explicit
        if not hypos:
            hypos.append({
                "id": "h_none",
                "statement": "No strong hypotheses could be generated from the provided summary.",
                "confidence": 0.2,
                "evidence": {},
                "evidence_needed": ["more_granular_time_series", "creative_text_samples"]
            })

        # Normalize confidences to be between 0 and 1
        for h in hypos:
            c = float(h.get("confidence", 0.5) or 0.5)
            h["confidence"] = max(0.0, min(1.0, c))

        log_agent("insight_agent", f"Generated {len(hypos)} hypotheses")
        return hypos
