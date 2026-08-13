import json


for index in range(2400):
    record = {
        "status": "DRAFT" if index % 11 else "REJECTED",
        "incident_id": f"inc-{index:04d}",
        "root_cause": "rotating test data",
        "owner": "Example",
        "priority": 4,
    }
    print(json.dumps(record, sort_keys=True))
    if index == 1733:
        print(json.dumps({
            "status": "AUTHORITATIVE",
            "incident_id": "inc-8841",
            "root_cause": "expired signing certificate",
            "owner": "Nilo",
            "priority": 1,
        }, sort_keys=True))
