# src/agents/evaluator.py

from agents.agent_base import AgentBase
from utils.logger import log_agent
from utils.metrics import pct_change, safe_mean, z_test_proportions


class EvaluatorAgent(AgentBase):
    """
    Evaluator Agent:
    - Validates hypotheses with numerical checks.
    - Outputs: hypothesis_id, validated=True/False, p_value, metric deltas, confidence.
    """

    def run(self, inputs):
        try:
            hypotheses = inputs.get("hypotheses") or inputs.get("payload", {}).get("hypotheses")
            summary = inputs.get("summary") or {}
            trend = summary.get("trend", [])
            campaigns = summary.get("campaign_summaries", [])
            global_summary = summary.get("global", {})

            if not hypotheses:
                raise ValueError("No hypotheses provided to EvaluatorAgent")

            log_agent("evaluator", f"Evaluating {len(hypotheses)} hypotheses")

            results = []
            for h in hypotheses:
                result = self._evaluate_single(h, summary, trend, campaigns, global_summary)
                results.append(result)

            final_conf = safe_mean([r["confidence"] for r in results])

            return {
                "status": "ok",
                "payload": {"evaluations": results},
                "confidence": float(final_conf)
            }

        except Exception as e:
            log_agent("evaluator", f"ERROR: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "confidence": 0.0
            }

    # ---------------------------------------------------------
    def _evaluate_single(self, hypothesis, summary, trend, campaigns, global_summary):
        """
        Evaluates one hypothesis depending on its ID.
        """

        h_id = hypothesis.get("id")
        statement = hypothesis.get("statement")
        base_conf = float(hypothesis.get("confidence", 0.5))

        # Default result
        result = {
            "hypothesis_id": h_id,
            "statement": statement,
            "validated": False,
            "p_value": None,
            "metrics": {},
            "confidence": base_conf
        }

        # ------------------ H1: ROAS TREND ------------------
        if h_id == "h_roas_trend" and trend:
            # compare first 7 days vs last 7 days (if available)
            try:
                first = trend[: min(7, len(trend))]
                last = trend[-min(7, len(trend)) :]

                first_roas = safe_mean([float(x.get("roas", 0)) for x in first])
                last_roas = safe_mean([float(x.get("roas", 0)) for x in last])

                change = pct_change(first_roas, last_roas)

                result["metrics"] = {
                    "first_period_roas": first_roas,
                    "last_period_roas": last_roas,
                    "pct_change": change
                }

                # If ROAS dropped significantly → validated
                if change < -0.05:  # >5% drop
                    result["validated"] = True
                    result["confidence"] = min(1.0, base_conf + 0.15)

            except Exception:
                pass

        # ------------------ H2: LOW CTR CREATIVE ISSUE ------------------
        if h_id == "h_low_ctr":
            low_ctr_list = summary.get("low_ctr_campaigns", [])
            if len(low_ctr_list) > 0:
                result["validated"] = True
                result["confidence"] = min(1.0, base_conf + 0.2)
                result["metrics"] = {"low_ctr_campaigns": low_ctr_list}

        # ------------------ H3: SPEND EFFICIENCY LOSS ------------------
        if h_id == "h_spend_efficiency":
            total_spend = float(global_summary.get("total_spend", 0))
            total_revenue = float(global_summary.get("total_revenue", 0))

            if total_spend > 0:
                roas_est = total_revenue / total_spend
            else:
                roas_est = 0

            result["metrics"] = {
                "spend": total_spend,
                "revenue": total_revenue,
                "roas": roas_est
            }

            if roas_est < 1.0:  # losing money
                result["validated"] = True
                result["confidence"] = min(1.0, base_conf + 0.1)

        # ------------------ H4: AUDIENCE FATIGUE ------------------
        if h_id == "h_audience_fatigue":
            # look for evidences: high impressions + low CTR
            fatigues = []

            for c in campaigns:
                ctr = float(c.get("ctr", 0))
                imps = float(c.get("impressions", 0))
                avg_ctr = float(global_summary.get("avg_ctr", 0.01))

                if imps > 1000 and ctr < avg_ctr * 0.7:
                    fatigues.append(c.get("campaign_name"))

            result["metrics"] = {"fatigue_candidates": fatigues}

            if len(fatigues) > 0:
                result["validated"] = True
                result["confidence"] = min(1.0, base_conf + 0.1)

        return result
