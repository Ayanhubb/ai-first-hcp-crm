"""Product catalog lookup + grounding (read-only)."""

from __future__ import annotations

import re
from uuid import UUID

from ..engine.exceptions import ToolError
from ..engine.retry import RetrySettings, call_with_retry
from ..state.schemas import CatalogProduct, ProductMatch
from .base import ProductCatalogPort


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def product_catalog_lookup(
    port: ProductCatalogPort,
    names_or_keywords: list[str],
    *,
    limit: int = 25,
    retry_settings: RetrySettings | None = None,
) -> list[CatalogProduct]:
    """Lookup catalog products by proposed names/keywords."""

    def _call() -> list[CatalogProduct]:
        try:
            return port.lookup(names_or_keywords, limit=limit)
        except ToolError:
            raise
        except Exception as exc:
            transient = "connection" in str(exc).lower() or "timeout" in str(exc).lower()
            raise ToolError(
                f"Catalog lookup failed: {exc}",
                code="CATALOG_DB_ERROR",
                fatal=True,
                transient=transient,
            ) from exc

    if not names_or_keywords:
        return []

    settings = retry_settings or RetrySettings()
    return call_with_retry(
        _call,
        max_retries=settings.tool_max_retries,
        settings=settings,
        retry_on=lambda e: isinstance(e, ToolError) and e.transient,
    )


def ground_product_candidates(
    port: ProductCatalogPort,
    candidates: list[str],
    *,
    min_confidence: float = 0.45,
    retry_settings: RetrySettings | None = None,
) -> tuple[list[ProductMatch], list[str]]:
    """Map LLM name candidates to grounded ProductMatch rows.

    Returns ``(matches, unmatched_names)``. Never invents UUIDs.
    """
    catalog = product_catalog_lookup(
        port,
        candidates,
        retry_settings=retry_settings,
    )
    by_norm: dict[str, CatalogProduct] = {}
    for product in catalog:
        by_norm[_normalize(product.name)] = product
        by_norm[_normalize(product.code)] = product

    matches: list[ProductMatch] = []
    unmatched: list[str] = []
    seen_ids: set[UUID] = set()

    for name in candidates:
        key = _normalize(name)
        product = by_norm.get(key)
        confidence = 0.95
        if product is None:
            # fuzzy contains
            for cat_key, cat_prod in by_norm.items():
                if key and (key in cat_key or cat_key in key):
                    product = cat_prod
                    confidence = 0.7
                    break
        if product is None:
            unmatched.append(name)
            continue
        if product.product_id in seen_ids:
            continue
        if confidence < min_confidence:
            unmatched.append(name)
            continue
        seen_ids.add(product.product_id)
        matches.append(
            ProductMatch(
                product_id=product.product_id,
                code=product.code,
                name=product.name,
                confidence=confidence,
            )
        )
    return matches, unmatched
