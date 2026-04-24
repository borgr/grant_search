#!/usr/bin/env python3
"""
Duplicate detection helper for grants.

Checks if a new grant entry matches an existing entry in found_grants.json
using multiple matching strategies to catch variations (different names, etc).
"""

import json
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class GrantDuplicateChecker:
    """Intelligent grant duplicate detection."""

    def __init__(self, found_grants_path: str = "found_grants.json"):
        """Initialize with path to found_grants.json."""
        self.found_grants_path = Path(found_grants_path)
        self.existing_grants: List[Dict] = []
        self._load_existing_grants()

    def _load_existing_grants(self):
        """Load existing grants from JSON."""
        if not self.found_grants_path.exists():
            print(f"⚠️  {self.found_grants_path} not found")
            return

        try:
            with open(self.found_grants_path, 'r') as f:
                data = json.load(f)
                self.existing_grants = data.get('grants', [])
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {self.found_grants_path}")
            self.existing_grants = []

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        return text.lower().strip() if text else ""

    def _exact_match(self, new_entry: Dict, existing: Dict) -> bool:
        """Check for exact name/org match."""
        new_name = self._normalize_text(new_entry.get('name', ''))
        new_org = self._normalize_text(new_entry.get('organization', ''))

        existing_name = self._normalize_text(existing.get('name', ''))
        existing_org = self._normalize_text(existing.get('organization', ''))

        return new_name == existing_name and new_org == existing_org

    def _fuzzy_match(self, new_entry: Dict, existing: Dict, threshold: float = 0.85) -> bool:
        """Fuzzy match on name and org."""
        new_name = self._normalize_text(new_entry.get('name', ''))
        new_org = self._normalize_text(new_entry.get('organization', ''))

        existing_name = self._normalize_text(existing.get('name', ''))
        existing_org = self._normalize_text(existing.get('organization', ''))

        # Match on name
        name_ratio = difflib.SequenceMatcher(None, new_name, existing_name).ratio()
        if name_ratio < threshold:
            return False

        # If orgs are both present, they should also match reasonably
        if new_org and existing_org:
            org_ratio = difflib.SequenceMatcher(None, new_org, existing_org).ratio()
            return org_ratio >= threshold

        return True

    def _url_match(self, new_entry: Dict, existing: Dict) -> bool:
        """Check if URLs match or have significant overlap."""
        new_url = new_entry.get('url', '').lower().strip()
        existing_url = existing.get('url', '').lower().strip()

        if not new_url or not existing_url:
            return False

        # Direct match
        if new_url == existing_url:
            return True

        # Check if URLs are from same domain and similar paths
        try:
            from urllib.parse import urlparse
            new_parsed = urlparse(new_url)
            existing_parsed = urlparse(existing_url)

            # Same domain + similar path suggests same program
            if new_parsed.netloc == existing_parsed.netloc:
                path_ratio = difflib.SequenceMatcher(
                    None,
                    new_parsed.path,
                    existing_parsed.path
                ).ratio()
                return path_ratio > 0.8
        except Exception:
            pass

        return False

    def _organization_match(self, new_entry: Dict, existing: Dict) -> bool:
        """Check for organization-only match (detect same org, different programs)."""
        new_org = self._normalize_text(new_entry.get('organization', ''))
        existing_org = self._normalize_text(existing.get('organization', ''))

        if not new_org or not existing_org:
            return False

        return new_org == existing_org

    def check_duplicate(self, new_entry: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Check if new entry is a duplicate.

        Returns:
            (is_duplicate, matching_existing_entry, reason)
        """
        if not new_entry:
            return False, None, "Empty entry"

        for existing in self.existing_grants:
            # Exact match (highest confidence)
            if self._exact_match(new_entry, existing):
                return True, existing, "Exact name and organization match"

            # URL match (high confidence)
            if self._url_match(new_entry, existing):
                return True, existing, "Same URL/program page"

            # Fuzzy match (medium confidence)
            if self._fuzzy_match(new_entry, existing, threshold=0.85):
                # Only report as duplicate if org also matches
                if self._organization_match(new_entry, existing):
                    return True, existing, f"Similar name and matching organization"

        return False, None, "No match found"

    def batch_check(self, entries: List[Dict]) -> Dict:
        """Check multiple entries and return report."""
        results = {
            'total': len(entries),
            'duplicates': [],
            'new': []
        }

        for entry in entries:
            is_dup, existing, reason = self.check_duplicate(entry)
            if is_dup:
                results['duplicates'].append({
                    'entry': entry,
                    'matched_existing': existing,
                    'reason': reason
                })
            else:
                results['new'].append(entry)

        return results

    def print_report(self, results: Dict):
        """Pretty print batch check results."""
        print(f"\n📊 Duplicate Check Report")
        print(f"{'='*60}")
        print(f"Total entries checked: {results['total']}")
        print(f"✅ New entries: {len(results['new'])}")
        print(f"⚠️  Duplicates found: {len(results['duplicates'])}\n")

        if results['duplicates']:
            print("Duplicates:")
            print("-" * 60)
            for item in results['duplicates']:
                print(f"❌ {item['entry'].get('name', 'Unknown')}")
                print(f"   Reason: {item['reason']}")
                print(f"   Existing: {item['matched_existing'].get('name', 'Unknown')} "
                      f"({item['matched_existing'].get('organization', 'Unknown')})")
                print()

        if results['new']:
            print("New entries to add:")
            print("-" * 60)
            for item in results['new']:
                print(f"✨ {item.get('name', 'Unknown')} ({item.get('organization', 'Unknown')})")
                print(f"   URL: {item.get('url', 'N/A')}")
                print()


def main():
    """CLI usage examples."""
    checker = GrantDuplicateChecker()

    # Example: check a single new entry
    new_grant = {
        "name": "NSF AI Research Grants",
        "organization": "National Science Foundation",
        "funding_amount_min": 50000,
        "funding_amount_max": 500000,
        "url": "https://www.nsf.gov/cgi-bin/browse-pubs.pl?ods_key=nsf21-550"
    }

    is_dup, existing, reason = checker.check_duplicate(new_grant)

    if is_dup:
        print(f"⚠️  DUPLICATE FOUND: {reason}")
        print(f"   Matches: {existing.get('name')} ({existing.get('organization')})")
    else:
        print(f"✨ NEW GRANT: {new_grant['name']}")


if __name__ == "__main__":
    main()
