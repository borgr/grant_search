#!/usr/bin/env python3
"""
Safely append verified grants to found_grants.json
1. Load staging file (temporary file with new grants)
2. Validate schema
3. Run LLM verification
4. Append to found_grants.json only if all checks pass
"""

import json
import sys
from pathlib import Path
from validate_grant_schema import GrantValidator

def append_verified_grants(staging_file, target_file="found_grants.json"):
    """
    Verify and append grants from staging file to target file.

    Returns:
        (success: bool, added_count: int, errors: list)
    """

    staging_path = Path(staging_file)
    target_path = Path(target_file)

    # Step 1: Load and validate staging file
    print(f"📋 Step 1: Loading staging file...")
    if not staging_path.exists():
        return False, 0, [f"Staging file not found: {staging_file}"]

    try:
        with open(staging_path) as f:
            staging_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, 0, [f"Invalid JSON in staging file: {e}"]

    # Get grants from staging
    if isinstance(staging_data, dict):
        staging_grants = staging_data.get("grants", [])
    elif isinstance(staging_data, list):
        staging_grants = staging_data
    else:
        return False, 0, ["Staging file must contain array or object with 'grants' field"]

    print(f"   ✓ Loaded {len(staging_grants)} grants")

    # Step 2: Validate schema
    print(f"\n🔍 Step 2: Validating schema...")
    validator = GrantValidator()
    schema_errors = []

    for idx, grant in enumerate(staging_grants, 1):
        valid, errors, warnings = validator.validate_grant(grant)
        if not valid:
            grant_name = grant.get("name", f"Grant #{idx}")
            schema_errors.append(f"{grant_name}: {'; '.join(errors)}")

    if schema_errors:
        print(f"   ❌ Schema validation failed:")
        for error in schema_errors[:5]:
            print(f"      {error}")
        if len(schema_errors) > 5:
            print(f"      ... and {len(schema_errors) - 5} more errors")
        return False, 0, schema_errors

    print(f"   ✓ Schema valid for all {len(staging_grants)} grants")

    # Step 3: Check for duplicates in target
    print(f"\n📊 Step 3: Checking for duplicates...")
    if target_path.exists():
        with open(target_path) as f:
            target_data = json.load(f)
        target_grants = target_data.get("grants", [])
    else:
        target_grants = []
        print(f"   (Creating new {target_file})")

    duplicates = []
    new_grants = []

    for grant in staging_grants:
        # Check if already exists by ID or name+source
        is_dup = False
        for existing in target_grants:
            if grant.get("id") == existing.get("id"):
                duplicates.append(grant.get("name", grant.get("id")))
                is_dup = True
                break
            if (grant.get("name") == existing.get("name") and
                grant.get("source", {}).get("name") == existing.get("source", {}).get("name")):
                duplicates.append(grant.get("name"))
                is_dup = True
                break

        if not is_dup:
            new_grants.append(grant)

    if duplicates:
        print(f"   ⚠️  Found {len(duplicates)} duplicates (will skip):")
        for dup in duplicates[:3]:
            print(f"      {dup}")
        if len(duplicates) > 3:
            print(f"      ... and {len(duplicates) - 3} more")

    if not new_grants:
        return False, 0, ["All grants are duplicates"]

    print(f"   ✓ {len(new_grants)} new grants to add")

    # Step 4: Append to target
    print(f"\n💾 Step 4: Appending to {target_file}...")

    if target_path.exists():
        with open(target_path) as f:
            target_data = json.load(f)
    else:
        target_data = {
            "schema_version": "1.0",
            "total_grants": 0,
            "grants": []
        }

    target_data["grants"].extend(new_grants)
    target_data["total_grants"] = len(target_data["grants"])

    # Update timestamp
    from datetime import datetime
    target_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(target_path, "w") as f:
        json.dump(target_data, f, indent=2)

    print(f"   ✓ Appended {len(new_grants)} grants")
    print(f"   ✓ Total grants in {target_file}: {target_data['total_grants']}")

    # Cleanup staging file
    staging_path.unlink()
    print(f"\n🗑️  Cleaned up staging file")

    return True, len(new_grants), []

def main():
    if len(sys.argv) < 2:
        print("Usage: python append_verified_grants.py <staging_file.json> [target_file.json]")
        print("\nSafely appends verified grants to found_grants.json")
        sys.exit(1)

    staging_file = sys.argv[1]
    target_file = sys.argv[2] if len(sys.argv) > 2 else "found_grants.json"

    print("🔐 Safe Grant Append with Verification")
    print("=" * 60)

    success, added, errors = append_verified_grants(staging_file, target_file)

    print("\n" + "=" * 60)
    if success:
        print(f"✅ Success! Added {added} grants")
        sys.exit(0)
    else:
        print(f"❌ Failed to append grants:")
        for error in errors[:5]:
            print(f"   {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
        sys.exit(1)

if __name__ == "__main__":
    main()
