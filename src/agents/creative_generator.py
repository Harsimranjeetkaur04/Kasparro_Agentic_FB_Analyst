# src/agents/creative_generator.py
"""
Creative Improvement Generator Agent (improved)

Key improvements:
- Normalize campaign names (collapse whitespace/punctuation, lowercase) to avoid near-duplicates.
- Prefer meaningful product terms (skip gender tokens like 'men', 'women') when building templates.
- Group creative messages by normalized campaign name for stable candidate generation.
- Keeps optional LLM rewrite hook behind config flag `use_llm` (default: False).
"""

from typing import Dict, Any, List
from agents.agent_base import AgentBase
from utils.logger import log_agent
from utils.io import load_csv
import os
import re
import pandas as pd

# sklearn is used for simple TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# gender / category tokens to avoid picking as 'primary'
GENDER_TOKENS = {"men", "women", "man", "woman", "male", "female", "girls", "boys", "kid", "kids", "mens", "womens"}

# --------------------- text helpers ---------------------
def _clean_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"http\S+", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _normalize_campaign_name(name: str) -> str:
    """
    Normalize campaign names to reduce duplication:
    - lowercase, trim, collapse spaces
    - remove repeated punctuation
    """
    if not isinstance(name, str):
        return ""
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9\s]", " ", n)   # drop punctuation
    n = re.sub(r"\s+", " ", n).strip()
    return n

def _top_n_terms(corpus: List[str], n: int = 5) -> List[str]:
    """
    Return top-n terms from corpus by TF-IDF average weights.
    """
    if not corpus:
        return []
    corpus_clean = [_clean_text(c) for c in corpus]
    try:
        vec = TfidfVectorizer(max_features=500, stop_words="english", ngram_range=(1, 2))
        X = vec.fit_transform(corpus_clean)
        scores = np.asarray(X.mean(axis=0)).ravel()
        terms = np.array(vec.get_feature_names_out())
        top_idx = np.argsort(scores)[::-1][:n]
        top_terms = terms[top_idx].tolist()
        # filter out tokens that are purely numeric or very short
        top_terms = [t for t in top_terms if re.search(r"[a-z]", t) and len(t) > 1]
        return top_terms
    except Exception:
        tokens = " ".join(corpus_clean).split()
        freq = {}
        for t in tokens:
            if len(t) <= 2:
                continue
            freq[t] = freq.get(t, 0) + 1
        sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [t for t, _ in sorted_terms[:n]]

def _choose_primary_term(terms: List[str]) -> str:
    """
    Prefer first non-gender token (and non-generic tokens) as primary.
    """
    for t in terms:
        # split on spaces for bigrams
        parts = t.split()
        # check if the token contains a non-gender meaningful word
        meaningful = False
        for p in parts:
            if p and p not in GENDER_TOKENS and len(p) > 2 and not p.isdigit():
                meaningful = True
                break
        if meaningful:
            return t
    # fallback to first term or a default
    return terms[0] if terms else "comfort"

def _choose_cta():
    return np.random.choice([
        "Shop Now", "Buy Now", "Get Yours", "Learn More", "Grab It", "See More", "Try Now", "Order Today"
    ])

def _templates_from_terms(terms: List[str]) -> List[Dict[str, str]]:
    """
    Create templates using terms. Uses safe defaults for missing terms.
    """
    primary = _choose_primary_term(terms) if terms else "comfort"
    secondary = terms[1] if len(terms) > 1 else "fit"
    tertiary = terms[2] if len(terms) > 2 else "breathable"

    templates = []
    templates.append({
        "headline": f"{primary.title()} — Limited Stock!",
        "message": f"Popular for its {secondary} and {tertiary}. Hurry — limited stock available.",
        "rationale": "urgency + product benefit"
    })
    templates.append({
        "headline": f"Feel the {primary.title()} Difference",
        "message": f"Experience {secondary} and all-day comfort with our {primary}.",
        "rationale": "benefit-led"
    })
    templates.append({
        "headline": f"Tired of Uncomfortable {primary.title()}?",
        "message": f"Switch to {primary} that offers {secondary} and stays breathable all day.",
        "rationale": "question hook"
    })
    templates.append({
        "headline": f"Thousands Love Our {primary.title()}",
        "message": f"Join thousands who chose comfort and fit — rated 4.7/5 by customers.",
        "rationale": "social proof"
    })
    templates.append({
        "headline": f"Today's Offer: {primary.title()} at 20% Off",
        "message": f"Get the perfect {secondary} and breathable {tertiary}. Limited time discount.",
        "rationale": "discount + urgency"
    })
    return templates

# --------------------- Agent ---------------------
class CreativeGenerator(AgentBase):
    """
    Creative Improvement Generator Agent (improved)
    """

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Summary contains low_ctr_campaigns
            summary = inputs.get("summary") or inputs.get("payload") or {}
            low_ctr_campaigns = summary.get("low_ctr_campaigns", []) or []
            csv_path = self.config.get("data_csv")

            if not csv_path or not os.path.exists(csv_path):
                log_agent("creative_generator", f"CSV not available at {csv_path}")
                return {"status": "error", "error": "CSV not found", "confidence": 0.0}

            df = load_csv(csv_path)
            if "creative_message" not in df.columns:
                log_agent("creative_generator", "CSV missing creative_message column")
                return {"status": "error", "error": "creative_message column missing", "confidence": 0.0}

            # Normalize campaign names in the dataframe to group correctly
            df = df.copy()
            df["campaign_norm"] = df["campaign_name"].apply(lambda x: _normalize_campaign_name(x or ""))

            # Build a mapping: normalized_campaign -> original_campaign_examples (first seen original values)
            camp_label_map = {}
            for orig, norm in zip(df["campaign_name"].astype(str).tolist(), df["campaign_norm"].tolist()):
                if norm not in camp_label_map:
                    camp_label_map[norm] = orig

            creatives_output = []

            # If user didn't provide low_ctr list, derive conservative set from summary
            if not low_ctr_campaigns:
                low_ctr_campaigns = summary.get("low_ctr_campaigns", []) or []

            # Convert provided low_ctr_campaigns to normalized form
            normalized_low_ctr = []
            for c in low_ctr_campaigns:
                normalized_low_ctr.append(_normalize_campaign_name(c))

            # If still empty, you can optionally take the bottom N campaigns by ctr
            if not normalized_low_ctr:
                # pick bottom 10 campaigns by ctr if available
                if "campaign_summaries" in summary and summary["campaign_summaries"]:
                    sorted_by_ctr = sorted(summary["campaign_summaries"], key=lambda x: float(x.get("ctr", 1.0)))
                    normalized_low_ctr = [_normalize_campaign_name(item.get("campaign_name","")) for item in sorted_by_ctr[:10]]
                else:
                    normalized_low_ctr = []

            # Produce creatives for each normalized campaign (unique)
            processed = set()
            for norm_c in normalized_low_ctr:
                if not norm_c or norm_c in processed:
                    continue
                processed.add(norm_c)

                # Filter by normalized campaign
                camp_df = df[df["campaign_norm"] == norm_c]
                camp_msgs = camp_df["creative_message"].dropna().astype(str).tolist()

                # If not enough campaign messages, fall back to broadly similar campaigns or global
                if len(camp_msgs) < 3:
                    # try to pick messages from rows that contain norm token in campaign_name
                    cand = df[df["campaign_norm"].str.contains(norm_c.split()[0])] if norm_c.split() else pd.DataFrame()
                    if cand is not None and not cand.empty:
                        camp_msgs = cand["creative_message"].dropna().astype(str).tolist()
                if len(camp_msgs) < 3:
                    # fallback to top global creatives
                    camp_msgs = df["creative_message"].dropna().astype(str).tolist()[:20]

                # extract terms and build templates
                top_terms = _top_n_terms(camp_msgs, n=6)
                templates = _templates_from_terms(top_terms)

                generated = []
                for t in templates[:5]:
                    candidate = {
                        "headline": t["headline"],
                        "message": t["message"],
                        "cta": _choose_cta(),
                        "rationale": t["rationale"],
                        "anchor_examples": camp_msgs[:3],
                        "confidence": round(min(0.9, 0.4 + len(camp_msgs) * 0.05), 2)
                    }

                    # Optional LLM rewrite (if enabled)
                    if self.config.get("use_llm", False):
                        # Placeholder for actual LLM call: keep safe, with timeout & retries when implemented
                        # Example: candidate = self._call_llm_refine(candidate, camp_msgs)
                        pass

                    generated.append(candidate)

                # map normalized campaign to a display label (first original found)
                display_label = camp_label_map.get(norm_c, norm_c)

                creatives_output.append({
                    "campaign": display_label,
                    "campaign_norm": norm_c,
                    "generated": generated
                })

            # If creatives_output empty (no low-ctr cams), produce a few global suggestions
            if not creatives_output:
                all_msgs = df["creative_message"].dropna().astype(str).tolist()
                top_terms = _top_n_terms(all_msgs, n=6)
                templates = _templates_from_terms(top_terms)
                generated = []
                for t in templates[:4]:
                    generated.append({
                        "headline": t["headline"],
                        "message": t["message"],
                        "cta": _choose_cta(),
                        "rationale": t["rationale"],
                        "anchor_examples": all_msgs[:3],
                        "confidence": 0.5
                    })
                creatives_output.append({
                    "campaign": "global_recommendations",
                    "campaign_norm": "global_recommendations",
                    "generated": generated
                })

            # compute final confidence as average of first candidates (safe fallback)
            if creatives_output:
                final_conf = np.mean([item["generated"][0]["confidence"] for item in creatives_output])
            else:
                final_conf = 0.0

            log_agent("creative_generator", f"Generated creatives for {len(creatives_output)} normalized campaigns")
            return {
                "status": "ok",
                "payload": {"creatives": creatives_output},
                "confidence": float(final_conf)
            }

        except Exception as e:
            log_agent("creative_generator", f"ERROR: {str(e)}")
            return {"status": "error", "error": str(e), "confidence": 0.0}
