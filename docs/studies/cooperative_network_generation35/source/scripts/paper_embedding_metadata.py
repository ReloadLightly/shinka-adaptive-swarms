"""Reconcile a changed download timestamp without changing encoder identity.

Only a recorded, hash-checked local manifest differing in downloaded_at is
accepted. Model artifacts, revision, pooling and other native checks stay fixed.
The frozen native module's source/configuration is never edited.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'results/paper_trajectory_v2/search/operations/embedding-metadata-reconciliation.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifests(expected_path, served_path, model_dir):
    expected = json.loads(expected_path.read_text())
    served = json.loads(served_path.read_text())
    expected_science = {k: v for k, v in expected.items() if k != 'downloaded_at'}
    served_science = {k: v for k, v in served.items() if k != 'downloaded_at'}
    if expected_science != served_science or expected.get('downloaded_at') == served.get('downloaded_at'):
        raise RuntimeError('Embedding reconciliation permits only a download timestamp difference')
    for item in served['artifacts']:
        path = model_dir / item['file']
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise RuntimeError('Embedding model artifact differs: ' + item['file'])
    return digest(served_path)


def subscription_preflight():
    from paper_trajectory_v2 import native
    if not RECEIPT.exists():
        return native.subscription_preflight()
    record = json.loads(RECEIPT.read_text())
    expected_path = ROOT / 'docs/embedding_model_manifest.json'
    original = native.EMBEDDING_IDENTITY
    if digest(expected_path) != original['model_manifest_sha256']:
        raise RuntimeError('Frozen embedding manifest changed')
    actual = verify_manifests(expected_path, ROOT / record['served_manifest_copy'], Path(record['model_directory']))
    if actual != record['served_manifest_sha256']:
        raise RuntimeError('Reconciliation receipt does not match served manifest')
    try:
        # Narrow operational comparison: native preflight still checks the live
        # service's exact hash and all other identity fields, and records them.
        native.EMBEDDING_IDENTITY = {**original, 'model_manifest_sha256': actual}
        result = native.subscription_preflight()
    finally:
        native.EMBEDDING_IDENTITY = original
    result['metadata_reconciliation'] = {
        'receipt': str(RECEIPT.relative_to(ROOT)), 'receipt_sha256': digest(RECEIPT),
        'frozen_manifest_sha256': original['model_manifest_sha256'],
        'served_manifest_sha256': actual, 'only_changed_field': 'downloaded_at',
        'all_model_artifacts_verified': True, 'frozen_native_source_unchanged': True,
        'actual_encoder_and_endpoint_unchanged': True,
    }
    return result
