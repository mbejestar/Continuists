import unittest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone

from backend.app.core.payment import calculate_marketplace_fees
from backend.app.core.storage import validate_file_upload
from backend.app.core.security import generate_continuum_id, generate_mission_continuum_id
from backend.app.models.mission import Mission
from backend.app.core.permissions import sanitize_mission_for_public_viewer

class TestContinuumSecurityAndPermissions(unittest.TestCase):
    """
    Automated security tests for Continuum:
    1. Continuum ID format and entropy.
    2. Fee calculation accuracy (8% direct vs 15% assisted).
    3. Document quota enforcement (50MB free vs unlimited premium).
    4. Server-side masking of confidential findings and documents.
    """

    def test_continuum_id_format(self):
        cnt_id = generate_continuum_id()
        self.assertTrue(cnt_id.startswith("CNT-"))
        self.assertEqual(len(cnt_id), 13) # CNT-XXXX-XXXX
        # Must not contain ambiguous characters 0, O, 1, I
        for forbidden in ["0", "O", "1", "I"]:
            self.assertNotIn(forbidden, cnt_id[4:])

    def test_mission_continuum_id_format(self):
        msn_id = generate_mission_continuum_id()
        self.assertTrue(msn_id.startswith("MSN-"))
        self.assertEqual(len(msn_id), 13)

    def test_direct_marketplace_fee_calculation(self):
        # Example from brief: R10,000 direct sale -> Continuum = R800 (8%), Seller = R9,200
        gross = Decimal("10000.00")
        breakdown = calculate_marketplace_fees(gross, "DIRECT")
        self.assertEqual(breakdown.platform_fee_rate, Decimal("0.08"))
        self.assertEqual(breakdown.platform_fee_amount, Decimal("800.00"))
        self.assertEqual(breakdown.seller_net_amount, Decimal("9200.00"))

    def test_assisted_marketplace_fee_calculation(self):
        # Example from brief: R10,000 assisted sale -> Continuum = R1,500 (15%), Seller = R8,500
        gross = Decimal("10000.00")
        breakdown = calculate_marketplace_fees(gross, "ASSISTED")
        self.assertEqual(breakdown.platform_fee_rate, Decimal("0.15"))
        self.assertEqual(breakdown.platform_fee_amount, Decimal("1500.00"))
        self.assertEqual(breakdown.seller_net_amount, Decimal("8500.00"))

    def test_free_tier_storage_limit_enforcement(self):
        # 50 MB limit test
        # Try to upload 51 MB on Free tier -> must raise HTTP 403
        oversized_bytes = b"0" * (51 * 1024 * 1024)
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            validate_file_upload(
                filename="large_drawing.pdf",
                content_type="application/pdf",
                file_bytes=oversized_bytes,
                current_mission_storage_bytes=0,
                user_subscription="FREE"
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("quota exceeded", ctx.exception.detail)

    def test_premium_tier_unlimited_storage_allowed(self):
        # Premium subscriber uploading 60 MB -> allowed
        payload = b"0" * (60 * 1024 * 1024)
        filename, mime, size, sha256 = validate_file_upload(
            filename="massive_karoo_survey.pdf",
            content_type="application/pdf",
            file_bytes=payload,
            current_mission_storage_bytes=100 * 1024 * 1024,
            user_subscription="PREMIUM"
        )
        self.assertEqual(size, 60 * 1024 * 1024)
        self.assertEqual(len(sha256), 64)

    def test_server_side_masking_for_public_viewer(self):
        """
        CRITICAL TEST:
        Ensure that sensitive findings, lessons learned, and documents
        are completely removed from the dictionary before serving to non-purchaser.
        """
        mission = Mission(
            id=uuid4(),
            continuum_id="MSN-TEST-1234",
            owner_id=uuid4(),
            heading="Deep Aquifer Geological Model",
            problem_statement="Groundwater depletion in Central Karoo",
            what_we_found="Secret seismic reflection data at coordinates -32.29, 22.45 showing 40M m3 reservoir",
            lessons_learned="Standard rotary drilling shears drill bit at layer 4 without synthetic diamond polymer",
            project_value_est=Decimal("5000000.00"),
            currency="ZAR",
            amount_spent=Decimal("1200000.00"),
            visibility="PUBLIC",
            collaboration_open=True,
            is_archived=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        sanitized = sanitize_mission_for_public_viewer(mission)
        
        # Heading & problem statement are visible
        self.assertEqual(sanitized["heading"], "Deep Aquifer Geological Model")
        self.assertEqual(sanitized["problem_statement"], "Groundwater depletion in Central Karoo")

        # SENSITIVE FIELDS MUST BE REDACTED (None / empty)
        self.assertIsNone(sanitized["what_we_found"])
        self.assertIsNone(sanitized["lessons_learned"])
        self.assertEqual(len(sanitized["documents"]), 0)
        self.assertTrue(sanitized["is_protected_marketplace"])
        self.assertIn("cryptographically locked", sanitized["protection_notice"])

if __name__ == "__main__":
    unittest.main()
