import unittest

from gmail_reply_policy import decide_auto_reply


OWNER = "muhammedayaan213@gmail.com"


def message(**changes):
    result = {"id": "msg-1", "thread_id": "thread-1",
              "from": "Friend <friend@example.com>", "to": OWNER,
              "label_ids": ["INBOX"], "headers": {}}
    result.update(changes)
    return result


class ReplyPolicyTests(unittest.TestCase):
    def decide(self, item, **kwargs):
        return decide_auto_reply(item, account_email=OWNER,
                                 allowed_senders={"friend@example.com"},
                                 already_handled=set(), **kwargs)

    def test_default_is_off_and_exact_allowlist_is_required(self):
        self.assertFalse(self.decide(message()).eligible)
        self.assertTrue(self.decide(message(), enabled=True).eligible)
        self.assertFalse(self.decide(message(**{"from": "stranger@example.com"}),
                                     enabled=True).eligible)
        self.assertFalse(decide_auto_reply(message(), account_email=OWNER,
                                           allowed_senders=set(),
                                           already_handled=set(), enabled=True).eligible)

    def test_duplicate_self_bulk_spam_and_missing_identity_refuse(self):
        cases = (message(id=""), message(to="other@example.com"),
                 message(**{"from": OWNER}), message(label_ids=["SPAM"]),
                 message(label_ids=None), message(headers=[]),
                 message(headers={"Auto-Submitted": "auto-replied"}),
                 message(headers={"List-Id": "news.example.com"}),
                 message(headers={"Precedence": "bulk"}),
                 message(**{"from": "noreply@example.com"}))
        for item in cases:
            with self.subTest(item=item):
                self.assertFalse(self.decide(item, enabled=True).eligible)
        self.assertFalse(decide_auto_reply(message(), account_email=OWNER,
                                           allowed_senders={"friend@example.com"},
                                           already_handled={"msg-1"},
                                           enabled=True).eligible)


if __name__ == "__main__":
    unittest.main()
