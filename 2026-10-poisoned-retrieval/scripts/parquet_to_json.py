"""Converts the Hugging Face copy of HotpotQA dev (distractor) to the original JSON layout used by the other scripts.
Usage: uv run --with pyarrow python3 -I parquet_to_json.py <validation.parquet> <out.json>
"""
import json, sys
import pyarrow.parquet as pq

rows = pq.read_table(sys.argv[1]).to_pylist()
out = [dict(_id=r["id"], question=r["question"], answer=r["answer"], type=r["type"], level=r["level"],
            supporting_facts=[[t, s] for t, s in zip(r["supporting_facts"]["title"], r["supporting_facts"]["sent_id"])],
            context=[[t, s] for t, s in zip(r["context"]["title"], r["context"]["sentences"])]) for r in rows]
json.dump(out, open(sys.argv[2], "w"))
print(len(out), "questions")
