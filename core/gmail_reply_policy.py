"""Fail-closed policy for a future, explicitly connected Gmail reply worker.

No Google credentials, mailbox access, AI generation, or send operation live
here. This module only decides whether a fetched message is even eligible for
an automatic reply; an independent OAuth adapter must still verify the sender,
thread and post-send Gmail state before claiming delivery.
"""

from __future__ import annotations

from dataclasses import dataclass
from email.utils import parseaddr


@dataclass(frozen=True)
class ReplyDecision:
    eligible: bool
    reason: str


def _address(value: str) -> str:
    return parseaddr(str(value or ""))[1].strip().casefold()


def decide_auto_reply(message: dict, *, account_email: str,
                      allowed_senders: set[str], already_handled: set[str],
                      enabled: bool = False) -> ReplyDecision:
    """Allow only a new, direct, non-automated message from an exact sender.

    The caller must never infer Gmail delivery merely from this decision.
    Empty allowlists or missing identifiers always refuse.
    """
    if not enabled:
        return ReplyDecision(False, "auto-reply disabled")
    if not isinstance(message, dict):
        return ReplyDecision(False, "invalid message")
    message_id = str(message.get("id") or "").strip()
    thread_id = str(message.get("thread_id") or "").strip()
    sender = _address(message.get("from", ""))
    recipient = _address(message.get("to", ""))
    owner = _address(account_email)
    allowlist = {_address(item) for item in allowed_senders}
    if not message_id or not thread_id or not owner or not sender:
        return ReplyDecision(False, "missing message identity")
    if message_id in already_handled:
        return ReplyDecision(False, "message already handled")
    if sender == owner:
        return ReplyDecision(False, "self-message")
    if sender not in allowlist:
        return ReplyDecision(False, "sender not allowlisted")
    if recipient != owner:
        return ReplyDecision(False, "not directly addressed to account")
    raw_labels = message.get("label_ids", [])
    raw_headers = message.get("headers", {})
    if (not isinstance(raw_labels, (list, tuple, set)) or
            not isinstance(raw_headers, dict)):
        return ReplyDecision(False, "invalid message metadata")
    labels = {str(item).upper() for item in raw_labels}
    if labels.intersection({"SPAM", "TRASH", "DRAFT", "SENT"}):
        return ReplyDecision(False, "excluded Gmail label")
    headers = {str(k).casefold(): str(v).strip().casefold()
               for k, v in raw_headers.items()}
    if (headers.get("auto-submitted", "no") != "no" or
            headers.get("list-id") or headers.get("list-unsubscribe") or
            headers.get("precedence") in {"bulk", "list", "junk"}):
        return ReplyDecision(False, "automated or mailing-list message")
    if sender.split("@", 1)[0] in {"no-reply", "noreply", "mailer-daemon", "postmaster"}:
        return ReplyDecision(False, "automated sender")
    return ReplyDecision(True, "eligible for a bounded reply draft")
