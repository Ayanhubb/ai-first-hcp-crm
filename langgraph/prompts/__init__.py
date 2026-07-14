"""Versioned prompt templates for the interaction assist graph."""

from .edit_notes import build_edit_messages
from .followup import build_followup_messages
from .history_summary import build_history_summary_messages
from .products import build_products_messages
from .repair import build_repair_messages
from .sentiment import build_sentiment_messages
from .summary import build_summary_messages
from .system import SYSTEM_CRM_ASSIST, system_message
from .topics import build_topics_messages

__all__ = [
    "SYSTEM_CRM_ASSIST",
    "system_message",
    "build_summary_messages",
    "build_sentiment_messages",
    "build_products_messages",
    "build_topics_messages",
    "build_followup_messages",
    "build_edit_messages",
    "build_history_summary_messages",
    "build_repair_messages",
]
