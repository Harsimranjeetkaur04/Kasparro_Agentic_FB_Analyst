# src/agents/data_agent.py

from agents.agent_base import AgentBase
from utils.io import load_csv
from utils.logger import log_agent
import pandas as pd
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Set


# ------------------ normalization helpers ------------------
COMMON_FIXES = {
    r"\blau(ch)?\b": "launch",
    r"\blau ch\b": "launch",
    r"\beve\s*yday\b": "everyday",
    r"\beve yday\b": "everyday",
    r"\beve y day\b": "everyday",
    r"\bevery ?day\b": "everyday",
    r"\bcomfort ?max\b": "comfortmax",
    r"\bcomfortmax\b": "comfortmax",
}


def _clean_text(s: str) -> str:
    """Lowercase, clean punctuation, collapse whitespace."""
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r"[\/\-_]+", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _merge_short_tokens(tokens: List[str]) -> List[str]:
    """Merge tiny fragments into previous token to fix breaks like 'la u nch'."""
    merged = []
    for t in tokens:
        if len(t) <= 2 and merged:
            merged[-1] = merged[-1] + t
        else:
            merged.append(t)
    return merged


def _apply_common_fixes(text: str) -> str:
    t = text
    for pat, repl in COMMON_FIXES.items():
        t = re.sub(pat, repl, t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalize_campaign_name(name: str) -> str:
    """
    Strong normalization:
    - clean text
    - split & merge tiny fragments
    - apply regex typo fixes
    """
    cleaned = _clean_text(name)
    tokens = cleaned.split()
    tokens = _merge_short_tokens(tokens)
    joined = " ".join(tokens)
    fixed = _apply_common_fixes(joined)
    return fixed.strip()


# ------------------ fuzzy helpers ------------------
def seq_ratio(a: str, b: str) -> float:
    """Sequence matcher ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def token_jaccard(a: str, b: str) -> float:
    """Jaccard similarity between token sets."""
    sa = set(a.split())
    sb = set(b.split())
    if not sa or not sb:
        return 0.0
    inter = sa.intersection(sb)
    union = sa.union(sb)
    return float(len(inter)) / float(len(union))


def combined_similarity(a: str, b: str) -> float:
    """
    Combine token Jaccard and sequence ratio for a robust similarity metric.
    Weighted average: 0.55 token_jaccard + 0.45 seq_ratio (empirically chosen).
    """
    return 0.55 * token_jaccard(a, b) + 0.45 * seq_ratio(a, b)


def build_fuzzy_groups(names: List[str], counts: Dict[str, int], threshold: float = 0.78) -> Dict[str, str]:
    """
    Greedy clustering: iterate names ordered by descending frequency; assign each name to an existing
    cluster if similarity >= threshold else start a new cluster. Returns mapping name->canonical_name.
    """
    sorted_names = sorted(names, key=lambda x: -counts.get(x, 0))
    groups: List[Tuple[str, Set[str]]] = []  # (canonical_name, set(members))
    mapping: Dict[str, str] = {}

    for name in sorted_names:
        assigned = False
        for i, (canon, members) in enumerate(groups):
            # compute similarity to canonical representative (canon)
            sim = combined_similarity(name, canon)
            if sim >= threshold:
                members.add(name)
                mapping[name] = canon
                assigned = True
                break
            # also check similarity to any member for safety (rare)
            if not assigned:
                for m in list(members):
                    if combined_similarity(name, m) >= threshold:
                        members.add(name)
                        mapping[name] = canon
                        assigned = True
                        break
            if assigned:
                break
        if not assigned:
            # create new group with name as canonical label
            groups.append((name, set([name])))
            mapping[name] = name

    # optional: pick a nicer canonical label for each group (choose most common original form)
    # but here canonical is the highest-frequency normalized name (already sorted)
    return mapping


# ------------------ DataAgent ------------------
class DataAgent(AgentBase):

    def run(self, inputs):
        try:
            csv_path = self.config["data_csv"]
            df = load_csv(csv_path)
            log_agent("data_agent", f"Loaded CSV at: {csv_path}")

            summary = self._summarize(df)
            return {
                "status": "ok",
                "payload": summary,
                "confidence": 0.95
            }

        except Exception as e:
            log_agent("data_agent", f"ERROR: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "confidence": 0.0
            }

    # ------------------------------------------------
    def _summarize(self, df: pd.DataFrame):
        # Required columns check
        required = {
            "spend", "revenue", "ctr", "roas",
            "clicks", "impressions", "campaign_name",
            "date", "creative_message"
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Dataset missing required columns: {missing}")

        df = df.copy()

        # ---------- Normalize campaign names ----------
        df["campaign_name"] = df["campaign_name"].fillna("").astype(str)
        df["campaign_norm"] = df["campaign_name"].apply(_normalize_campaign_name)

        # ---------- Build frequency counts for normalized names ----------
        norm_counts = Counter(df["campaign_norm"].tolist())

        # ---------- Build fuzzy mapping name -> canonical_norm ----------
        unique_norms = list(norm_counts.keys())
        # When few unique entries, skip expensive grouping
        SIMILARITY_THRESHOLD = float(self.config.get("similarity_threshold", 0.78))
        if len(unique_norms) <= 1:
            fuzzy_map = {n: n for n in unique_norms}
        else:
            fuzzy_map = build_fuzzy_groups(unique_norms, norm_counts, threshold=SIMILARITY_THRESHOLD)

        # ---------- Apply fuzzy canonicalization ----------
        df["campaign_canon"] = df["campaign_norm"].map(lambda x: fuzzy_map.get(x, x))

        # ---------- Global Metrics ----------
        global_summary = {
            "total_spend": float(df["spend"].sum()),
            "total_revenue": float(df["revenue"].sum()),
            "avg_ctr": float(df["ctr"].mean()),
            "avg_roas": float(df["roas"].mean()),
            "total_clicks": int(df["clicks"].sum()),
            "total_impressions": int(df["impressions"].sum()),
            "date_range": {
                "min": str(df["date"].min()),
                "max": str(df["date"].max())
            }
        }

        # ---------- Daily Trend ----------
        daily_trend = (
            df.groupby("date")
              .agg({
                  "roas": "mean",
                  "ctr": "mean",
                  "spend": "sum",
                  "clicks": "sum",
                  "impressions": "sum"
              })
              .reset_index()
              .sort_values("date")
              .to_dict(orient="records")
        )

        # ---------- Campaign Summary (grouped by canonical name) ----------
        campaign_agg = (
            df.groupby("campaign_canon")
              .agg({
                  "ctr": "mean",
                  "roas": "mean",
                  "spend": "sum",
                  "revenue": "sum",
                  "clicks": "sum",
                  "impressions": "sum",
                  "campaign_name": "first"  # representative original label
              })
              .reset_index()
        )

        campaign_summaries = []
        for _, row in campaign_agg.iterrows():
            campaign_summaries.append({
                "campaign_canon": row["campaign_canon"],
                "campaign_display": row["campaign_name"],
                "ctr": float(row["ctr"]),
                "roas": float(row["roas"]),
                "spend": float(row["spend"]),
                "revenue": float(row["revenue"]),
                "clicks": int(row["clicks"]),
                "impressions": int(row["impressions"]),
            })

        # ---------- LOW CTR campaigns (canonical strings) ----------
        if len(campaign_agg) == 0:
            low_ctr = []
        else:
            ctr_threshold = campaign_agg["ctr"].quantile(0.25)
            low_ctr = (
                campaign_agg[campaign_agg["ctr"] <= ctr_threshold]["campaign_canon"]
                .tolist()
            )

        # ---------- Result ----------
        return {
            "global": global_summary,
            "trend": daily_trend,
            "campaign_summaries": campaign_summaries,
            "low_ctr_campaigns": low_ctr
        }
