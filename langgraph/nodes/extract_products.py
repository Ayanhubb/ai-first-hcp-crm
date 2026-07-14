"""extract_products node — LLM candidates + catalog grounding."""

from __future__ import annotations

from typing import Any

from ..prompts.products import build_products_messages
from ..engine.structured import invoke_structured, meta_update
from ..state.interaction_state import InteractionAssistState, append_error, coerce_product_matches
from ..state.schemas import ProductCandidatesOutput
from ..tools.product_catalog_tool import ground_product_candidates
from ._common import NodeContext, catch_node, merge_updates, require_notes


def make_extract_products_node(ctx: NodeContext):
    def extract_products(state: InteractionAssistState) -> dict[str, Any]:
        notes = require_notes(state)
        if not notes:
            return {"products": []}

        catalog = ctx.tools.catalog
        catalog_hint: list[str] | None = None
        if catalog is not None:
            try:
                catalog_hint = catalog.list_names(limit=40)
            except Exception:
                catalog_hint = None

        messages = build_products_messages(notes=notes, catalog_hint=catalog_hint)
        try:
            parsed, usage, raw = invoke_structured(
                ctx.llm,
                node="extract_products",
                schema=ProductCandidatesOutput,
                messages=messages,
                temperature=ctx.llm.config.extraction_temperature,
                max_tokens=ctx.llm.config.max_tokens_extraction,
            )
        except Exception as exc:
            return append_error(
                "extract_products",
                "PRODUCTS_LLM_FAILED",
                str(exc),
                fatal=False,
            )

        updates: dict[str, Any] = {
            **meta_update("extract_products", usage, model_name=ctx.llm.model_name),
            "raw_llm_fragments": {"extract_products": raw[:2000]},
        }

        if not parsed.candidates:
            updates["products"] = []
            return updates

        if catalog is None:
            return merge_updates(
                updates,
                {"products": []},
                append_error(
                    "extract_products",
                    "TOOL_NOT_CONFIGURED",
                    "Catalog port missing; cannot ground product IDs",
                    fatal=False,
                ),
            )

        matches, unmatched = ground_product_candidates(catalog, parsed.candidates)
        updates["products"] = coerce_product_matches(matches)
        if unmatched:
            updates = merge_updates(
                updates,
                append_error(
                    "extract_products",
                    "PRODUCTS_UNMATCHED",
                    f"Unmatched product names: {', '.join(unmatched)}",
                    fatal=False,
                ),
            )
        return updates

    return catch_node("extract_products", extract_products)
