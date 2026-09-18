"""Exact, recorded operational-source compatibility; scientific hashes stay frozen."""
from __future__ import annotations

import hashlib
import json

AMENDMENT = 'experiments/paper_trajectory_v2/recovery_identity_amendment_v2.json'
HELPER = 'scripts/paper_operational_compatibility.py'
MANIFEST = 'campaigns/paper_trajectory_v2.json'
SCIENTIFIC_IDENTITY = '2e539b8491c4640187622a15da826280e19ee9322e1be5a2bf02f2d6485c82cc'
ORIGINAL = {
    'paper_trajectory_v2/evaluate.py': '134ff78cca663ce152f31fe2a46ea8c3d6be68d9e22aecb89ffc03dc8ccc1091',
    'paper_trajectory_v2/gate.py': 'a2e9958249de21cee1d3417465a17fa6ebee5b84e51a31ec01a76d23935622f3',
    'paper_trajectory_v2/recovery.py': 'bd76a28337a6897f4a95acace78b8000a15be25c4ec2d0e189032fecae949979',
    'paper_trajectory_v2/native.py': 'f288ebfb9c31c776cdacb452275796730c0c8ba0b3d626712c87cdb7bdf588ed',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def resolved_digest(relative, expected, read):
    """Accept original bytes or exactly the registered, archived operational edit.

    `read` reads repository-relative bytes from a checkout or a Git export.
    No change to engine, evaluation arithmetic, panel, policy or prompts is allowed.
    """
    actual = sha(read(relative))
    if actual == expected:
        return expected
    if ORIGINAL.get(relative) != expected:
        raise RuntimeError('Frozen scientific artifact changed: ' + relative)
    manifest = json.loads(read(MANIFEST))
    registration = manifest.get('recovery_identity_operational_amendment', {})
    data = read(AMENDMENT)
    amendment = json.loads(data)
    if (registration != {'path': AMENDMENT, 'sha256': sha(data)}
            or manifest.get('campaign_id') != 'paper_trajectory_v2'
            or amendment.get('schema') != 'paper-recovery-process-identity-amendment-v2'
            or amendment.get('scientific_identity') != SCIENTIFIC_IDENTITY
            or amendment.get('scientific_effect') != 'none'
            or amendment.get('helper_sha256') != sha(read(HELPER))
            or set(amendment.get('sources', {})) != set(ORIGINAL)):
        raise RuntimeError('Unregistered or inconsistent recovery identity amendment')
    for path, original in ORIGINAL.items():
        record = amendment['sources'][path]
        archived = 'experiments/paper_trajectory_v2/recovery_identity_v1_originals/' + path
        if (record.get('original_sha256') != original
                or record.get('original_path') != archived
                or sha(read(archived)) != original
                or sha(read(path)) != record.get('executed_sha256')):
            raise RuntimeError('Recovery operational source/evidence changed: ' + path)
    return actual
