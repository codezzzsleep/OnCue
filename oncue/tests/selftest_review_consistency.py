#!/usr/bin/env python3
"""Offline consistency test: build/review.json must match the shipped bundle.

The review packet is what external reviewers read. If its card_source drifts
from bundle/main.splash, or its version drifts from bundle/manifest.json, the
packet describes a different app than the one in the repo. This test keeps the
two in lockstep in the existing CI selftest job; no host, network or display.
"""
import sys
sys.dont_write_bytecode = True

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'build' / 'review.json'
SOURCE = ROOT / 'bundle' / 'main.splash'
MANIFEST = ROOT / 'bundle' / 'manifest.json'


class ReviewConsistency(unittest.TestCase):
    def setUp(self):
        self.review = json.loads(REVIEW.read_text(encoding='utf-8'))
        self.source = SOURCE.read_text(encoding='utf-8')
        self.manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))

    def test_card_source_matches_bundle_verbatim(self):
        card_source = self.review.get('card_source')
        self.assertIsInstance(card_source, str, 'review.json card_source must be a string')
        self.assertEqual(
            card_source, self.source,
            'build/review.json card_source differs from bundle/main.splash; '
            'regenerate the review packet from the current source')

    def test_version_matches_manifest(self):
        version = self.review.get('version')
        self.assertEqual(
            version, self.manifest.get('version'),
            'build/review.json version differs from bundle/manifest.json version')

    def test_embedded_manifest_version_matches(self):
        embedded = self.review.get('manifest')
        if isinstance(embedded, str):
            embedded = json.loads(embedded)
        self.assertEqual(
            embedded.get('version'), self.manifest.get('version'),
            'build/review.json embedded manifest version differs from bundle/manifest.json')


if __name__ == '__main__':
    unittest.main()
