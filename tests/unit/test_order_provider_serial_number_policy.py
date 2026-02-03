import pytest

from xscanner.server.order.providers.base import OrderIssuerProvider
from xscanner.server.order.providers.registry import get_provider_by_issuer


def test_a_mark_order_confirmation_disables_serial_number_expected() -> None:
    provider = get_provider_by_issuer("a-mark")
    assert provider is not None
    assert (
        provider.effective_serial_number_expected(
            requested=True,
            doc_type="order_confirmation",
        )
        is False
    )


@pytest.mark.parametrize("doc_type", ["invoice", "delivery_note", "unknown", ""])
def test_a_mark_other_doc_types_do_not_override_serial_number_expected(doc_type: str) -> None:
    provider = get_provider_by_issuer("a-mark")
    assert provider is not None
    assert (
        provider.effective_serial_number_expected(
            requested=True,
            doc_type=doc_type,
        )
        is True
    )


def test_provider_default_policy_passthrough() -> None:
    provider = OrderIssuerProvider(
        issuer="example",
        match_needles_upper=("EXAMPLE",),
    )
    assert provider.effective_serial_number_expected(requested=True, doc_type="invoice") is True
    assert provider.effective_serial_number_expected(requested=False, doc_type="invoice") is False
