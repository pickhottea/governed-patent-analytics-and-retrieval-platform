Recommended run order (inside project root):

1) Build chunks from recovered Google raw data
python scripts/semantic/step_c2_build_chunks_v2.py --run_id 20260221T200902Z__semantic_exp_v2

2) Validate chunks
python scripts/semantic/validate_chunks_v2.py --run_id 20260221T200902Z__semantic_exp_v2

3) Build Chroma with full Google 150 + bge-m3 (safer CPU settings)
python scripts/semantic/step_c3_embed_chunks_google150_bgem3_v2.py \
  --run_id 20260221T200902Z__semantic_exp_v2 \
  --model_key bge-m3 \
  --device cpu \
  --expected_families 150 \
  --encode_batch_size 4 \
  --upsert_batch_size 4 \
  --max_seq_length 512

If your laptop struggles, lower both batch sizes to 2.
