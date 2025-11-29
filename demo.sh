#!/usr/bin/env bash
# demo.sh — run a short demo: pipeline + print top insights + one creative sample (no jq)
set -euo pipefail

QUERY=${1:-"Analyze ROAS drop in last 7 days"}
PYTHON=${PYTHON:-python}

echo "Running demo query:"
echo "  $QUERY"
echo "---------------------------------------"
$PYTHON src/run.py "$QUERY"

echo
echo "Reports generated in ./reports"
echo

# Use Python to pretty-print validated insights and a creative sample
$PYTHON - <<'PY'
import json, sys, os
ins_path = os.path.join("reports","insights.json")
cr_path = os.path.join("reports","creatives.json")

def pretty_print_insights(p):
    if not os.path.exists(p):
        print("No insights report found at", p)
        return
    r = json.load(open(p))
    v = r.get("validated_insights", [])
    print("Validated insights (count={}):".format(len(v)))
    if not v:
        print("  No validated insights")
    else:
        for i, item in enumerate(v[:5],1):
            hyp = item.get("hypothesis",{})
            ev = item.get("evaluation",{})
            stmt = hyp.get("statement") or hyp.get("id") or ("hypothesis_"+str(i))
            conf = ev.get("confidence", ev.get("score", "N/A"))
            reasoning = hyp.get("reasoning", hyp.get("explanation",""))
            print(f"{i}. {stmt} (conf={conf})")
            if reasoning:
                print(f"   Reasoning: {reasoning}")
    print()

def pretty_print_creative_sample(p):
    if not os.path.exists(p):
        print("No creatives report found at", p)
        return
    r = json.load(open(p))
    creatives = r.get("creatives", [])
    print("Creative buckets (count={}):".format(len(creatives)))
    if not creatives:
        print("  No creatives")
    else:
        first = creatives[0]
        campaign = first.get("campaign", "<no-campaign>")
        generated = first.get("generated", [])
        print(f"Sample creative for campaign: {campaign}")
        if generated:
            g = generated[0]
            print("  Headline:", g.get("headline"))
            print("  Message:", g.get("message"))
            print("  CTA:", g.get("cta"))
            print("  Confidence:", g.get("confidence"))
        else:
            print("  No generated creatives for this campaign")
    print()

pretty_print_insights(ins_path)
pretty_print_creative_sample(cr_path)
PY

echo "Demo complete."
