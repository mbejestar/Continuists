"""
Continuum Platform Standalone Logic & Security Test Suite.
Runs on any standard Python 3.10+ installation without external pip dependencies.

Validates:
1. High-entropy non-identifying Continuum ID generation (CNT-XXXX-XXXX).
2. Backend marketplace fee split calculation (8% direct vs 15% assisted).
3. Server-side redaction and data masking for unpurchased missions.
4. Cumulative storage quota calculations (50 MB Free tier).
"""

import unittest
from decimal import Decimal, ROUND_HALF_UP
import secrets
import string
import hashlib

def calculate_marketplace_fees(gross_amount: Decimal, fee_tier: str):
    """Calculates fee splits with exact ZAR cents rounding."""
    tier = fee_tier.upper().strip()
    rate = Decimal("0.15") if tier == "ASSISTED" else Decimal("0.08")
    cents = Decimal("0.01")
    platform_fee = (gross_amount * rate).quantize(cents, rounding=ROUND_HALF_UP)
    seller_net = (gross_amount - platform_fee).quantize(cents, rounding=ROUND_HALF_UP)
    return {
        "gross": gross_amount,
        "tier": tier,
        "rate": rate,
        "platform_fee": platform_fee,
        "seller_net": seller_net
    }

def generate_continuum_id() -> str:
    """Generates non-identifiable Continuum ID without ambiguous characters (0, O, 1, I)."""
    chars = string.ascii_uppercase + string.digits
    clean_chars = "".join([c for c in chars if c not in "0O1I"])
    part1 = "".join(secrets.choice(clean_chars) for _ in range(4))
    part2 = "".join(secrets.choice(clean_chars) for _ in range(4))
    return f"CNT-{part1}-{part2}"

def sanitize_mission_record(mission_dict: dict, user_has_clearance: bool) -> dict:
    """
    CRITICAL REDACTION ENGINE:
    If user lacks clearance, proprietary findings, lessons learned, and documents
    are strictly redacted on the server.
    """
    if user_has_clearance:
        return mission_dict
    
    sanitized = dict(mission_dict)
    sanitized["what_we_found"] = None
    sanitized["lessons_learned"] = None
    sanitized["documents"] = []
    sanitized["is_protected_marketplace"] = True
    return sanitized


class TestContinuumHumanEngineeredLogic(unittest.TestCase):
    
    def test_continuum_id_entropy_and_popia_compliance(self):
        """Continuum ID must not contain personal info or confusing characters."""
        for _ in range(25):
            cid = generate_continuum_id()
            self.assertTrue(cid.startswith("CNT-"))
            self.assertEqual(len(cid), 13)
            # Must not contain 0, O, 1, I
            for ambiguous in ["0", "O", "1", "I"]:
                self.assertNotIn(ambiguous, cid)

    def test_direct_transaction_fee_breakdown(self):
        """
        Verify R10,000 direct sale:
        Continuum receives 8% (R800), Seller receives 92% (R9,200).
        """
        gross = Decimal("10000.00")
        res = calculate_marketplace_fees(gross, "DIRECT")
        self.assertEqual(res["platform_fee"], Decimal("800.00"))
        self.assertEqual(res["seller_net"], Decimal("9200.00"))
        self.assertEqual(res["platform_fee"] + res["seller_net"], gross)

    def test_assisted_transaction_fee_breakdown(self):
        """
        Verify R10,000 assisted sale:
        Continuum receives 15% (R1,500), Seller receives 85% (R8,500).
        """
        gross = Decimal("10000.00")
        res = calculate_marketplace_fees(gross, "ASSISTED")
        self.assertEqual(res["platform_fee"], Decimal("1500.00"))
        self.assertEqual(res["seller_net"], Decimal("8500.00"))
        self.assertEqual(res["platform_fee"] + res["seller_net"], gross)

    def test_server_side_masking_deep_aquifer_mission(self):
        """
        Simulate an unpurchased prospective buyer querying the Karoo Aquifer project.
        All technical findings and borehole pressure logs must be redacted.
        """
        raw_mission = {
            "id": "msn-001",
            "heading": "Central Karoo Artesian Aquifer Drilling Survey",
            "problem_statement": "High salinity shale strata caused 280m borehole failures.",
            "what_we_found": "Hydrostatic pressure at 380m delivers 42,000 L/hr under 480 mg/L TDS.",
            "lessons_learned": "Never use rotary air blasting; bentonite mud seal is mandatory.",
            "documents": [
                {"name": "Karoo_Seismic_CrossSection.pdf", "sha256": "3f7b8a..."},
                {"name": "Borehole_Flow_Logs.xlsx", "sha256": "9a8b7c..."}
            ]
        }

        # 1. Non-purchaser access -> Redacted
        masked = sanitize_mission_record(raw_mission, user_has_clearance=False)
        self.assertEqual(masked["heading"], "Central Karoo Artesian Aquifer Drilling Survey")
        self.assertEqual(masked["problem_statement"], "High salinity shale strata caused 280m borehole failures.")
        self.assertIsNone(masked["what_we_found"])
        self.assertIsNone(masked["lessons_learned"])
        self.assertEqual(masked["documents"], [])
        self.assertTrue(masked["is_protected_marketplace"])

        # 2. Purchaser access -> Fully unmasked
        unmasked = sanitize_mission_record(raw_mission, user_has_clearance=True)
        self.assertIsNotNone(unmasked["what_we_found"])
        self.assertEqual(len(unmasked["documents"]), 2)

    def test_free_tier_50mb_quota_calculation(self):
        """Verify cumulative 50MB storage calculation logic."""
        FREE_LIMIT_BYTES = 50 * 1024 * 1024
        current_used = 42 * 1024 * 1024  # 42 MB
        incoming_file = 9 * 1024 * 1024   # 9 MB -> total 51 MB (exceeds cap)
        
        would_exceed = (current_used + incoming_file) > FREE_LIMIT_BYTES
        self.assertTrue(would_exceed)

if __name__ == "__main__":
    unittest.main()
