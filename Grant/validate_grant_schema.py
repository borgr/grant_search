#!/usr/bin/env python3
"""
Validate grant JSON against the schema defined in process_grant.md
Checks structure, field types, and required fields.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Schema requirements
REQUIRED_FIELDS = [
    "id", "name", "applicant_need", "source", "award",
    "deadline", "eligibility", "requirements", "recurring", "notes", "tags"
]

APPLICANT_NEEDS = [
    "personal_stipend", "student_support", "research_project",
    "lab_operations", "org_operations", "startup_capital",
    "infrastructure", "competition_prize", "community_support",
    "conference_travel", "compute_access", "mixed"
]

AWARD_TYPES = ["cash", "gpu", "equity-waiver", "other"]
SOURCE_TYPES = ["website", "email", "recommendation", "partnership"]
RECURRING_TYPES = ["yearly", "quarterly", "one-time", "anytime", "no", "other"]
STAGES = ["early-stage", "growth", "all"]
EFFORT_LEVELS = ["low", "medium", "high"]

class GrantValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_grant(self, grant):
        """Validate a single grant entry"""
        self.errors = []
        self.warnings = []

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in grant:
                self.errors.append(f"Missing required field: {field}")

        # Validate each field
        if "id" in grant:
            self._validate_id(grant["id"])
        if "name" in grant:
            self._validate_name(grant["name"])
        if "applicant_need" in grant:
            self._validate_applicant_need(grant["applicant_need"])
        if "source" in grant:
            self._validate_source(grant["source"])
        if "award" in grant:
            self._validate_award(grant["award"])
        if "deadline" in grant:
            self._validate_deadline(grant["deadline"])
        if "eligibility" in grant:
            self._validate_eligibility(grant["eligibility"])
        if "requirements" in grant:
            self._validate_requirements(grant["requirements"])
        if "recurring" in grant:
            self._validate_recurring(grant["recurring"])
        if "notes" in grant:
            self._validate_notes(grant["notes"])
        if "tags" in grant:
            self._validate_tags(grant["tags"])

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_id(self, id_val):
        if not isinstance(id_val, str):
            self.errors.append(f"id must be string, got {type(id_val).__name__}")
        elif not id_val.startswith("grant-"):
            self.warnings.append(f"id should start with 'grant-': {id_val}")

    def _validate_name(self, name):
        if not isinstance(name, str):
            self.errors.append(f"name must be string, got {type(name).__name__}")
        elif len(name) < 5:
            self.warnings.append(f"name seems too short: '{name}'")

    def _validate_applicant_need(self, need):
        if not isinstance(need, str):
            self.errors.append(f"applicant_need must be string, got {type(need).__name__}")
        elif need not in APPLICANT_NEEDS:
            self.errors.append(f"applicant_need '{need}' not in allowed values: {APPLICANT_NEEDS}")

    def _validate_source(self, source):
        if not isinstance(source, dict):
            self.errors.append(f"source must be object, got {type(source).__name__}")
            return

        required = ["name", "url", "discovered_date", "source_type"]
        for field in required:
            if field not in source:
                self.errors.append(f"source.{field} is required")

        if "url" in source and not isinstance(source["url"], str):
            self.errors.append(f"source.url must be string")

        if "discovered_date" in source:
            self._validate_date(source["discovered_date"], "source.discovered_date")

        if "source_type" in source and source["source_type"] not in SOURCE_TYPES:
            self.errors.append(f"source.source_type '{source['source_type']}' not in {SOURCE_TYPES}")

    def _validate_award(self, award):
        if not isinstance(award, dict):
            self.errors.append(f"award must be object, got {type(award).__name__}")
            return

        required = ["type", "min_amount", "max_amount", "currency"]
        for field in required:
            if field not in award:
                self.errors.append(f"award.{field} is required")

        if "type" in award and award["type"] not in AWARD_TYPES:
            self.errors.append(f"award.type '{award['type']}' not in {AWARD_TYPES}")

        if "min_amount" in award and not isinstance(award["min_amount"], (int, float)):
            self.errors.append(f"award.min_amount must be number")
        if "max_amount" in award and not isinstance(award["max_amount"], (int, float)):
            self.errors.append(f"award.max_amount must be number")

        if "min_amount" in award and "max_amount" in award:
            if award["min_amount"] > award["max_amount"]:
                self.errors.append(f"award.min_amount ({award['min_amount']}) > max_amount ({award['max_amount']})")

    def _validate_deadline(self, deadline):
        if not isinstance(deadline, str):
            self.errors.append(f"deadline must be string, got {type(deadline).__name__}")
        elif deadline != "Rolling" and deadline != "TBD":
            self._validate_date(deadline, "deadline")

    def _validate_eligibility(self, eligibility):
        if not isinstance(eligibility, dict):
            self.errors.append(f"eligibility must be object, got {type(eligibility).__name__}")
            return

        required = ["stage", "team_size_min", "team_size_max", "geography", "restrictions", "special_requirements"]
        for field in required:
            if field not in eligibility:
                self.errors.append(f"eligibility.{field} is required")

        if "stage" in eligibility:
            if not isinstance(eligibility["stage"], list):
                self.errors.append(f"eligibility.stage must be array")
            else:
                for s in eligibility["stage"]:
                    if s not in STAGES:
                        self.errors.append(f"eligibility.stage '{s}' not in {STAGES}")

    def _validate_requirements(self, requirements):
        if not isinstance(requirements, dict):
            self.errors.append(f"requirements must be object, got {type(requirements).__name__}")
            return

        required = ["application_effort", "key_requirements", "focus_areas"]
        for field in required:
            if field not in requirements:
                self.errors.append(f"requirements.{field} is required")

        if "application_effort" in requirements and requirements["application_effort"] not in EFFORT_LEVELS:
            self.errors.append(f"requirements.application_effort not in {EFFORT_LEVELS}")

    def _validate_recurring(self, recurring):
        if not isinstance(recurring, str):
            self.errors.append(f"recurring must be string, got {type(recurring).__name__}")
        elif recurring not in RECURRING_TYPES:
            self.errors.append(f"recurring '{recurring}' not in {RECURRING_TYPES}")

    def _validate_notes(self, notes):
        if not isinstance(notes, str):
            self.errors.append(f"notes must be string, got {type(notes).__name__}")

    def _validate_tags(self, tags):
        if not isinstance(tags, list):
            self.errors.append(f"tags must be array, got {type(tags).__name__}")

    def _validate_date(self, date_str, field_name):
        """Validate date format YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.errors.append(f"{field_name} must be YYYY-MM-DD format, got '{date_str}'")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_grant_schema.py <file.json>")
        print("\nValidates grant JSON file against schema.")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    # Check if it's an array or has a 'grants' field
    if isinstance(data, dict):
        grants = data.get("grants", [])
    elif isinstance(data, list):
        grants = data
    else:
        print("❌ File must contain array of grants or object with 'grants' field")
        sys.exit(1)

    validator = GrantValidator()
    total_errors = 0
    total_warnings = 0

    print(f"📋 Validating {len(grants)} grants from {file_path.name}\n")

    for idx, grant in enumerate(grants, 1):
        valid, errors, warnings = validator.validate_grant(grant)

        if not valid or warnings:
            grant_name = grant.get("name", f"Grant #{idx}")
            if not valid:
                print(f"❌ {grant_name}")
                for error in errors:
                    print(f"   ERROR: {error}")
                total_errors += len(errors)
            if warnings:
                print(f"⚠️  {grant_name}")
                for warning in warnings:
                    print(f"   WARNING: {warning}")
                total_warnings += len(warnings)

    print(f"\n{'='*60}")
    print(f"Total errors: {total_errors}")
    print(f"Total warnings: {total_warnings}")

    if total_errors > 0:
        print("\n❌ Validation FAILED")
        sys.exit(1)
    else:
        print("\n✅ Validation PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
