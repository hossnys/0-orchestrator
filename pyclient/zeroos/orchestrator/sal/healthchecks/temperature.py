from js9  import j

descr = """
Checks temperature of the system.
Result will be shown in the "Temperature" section of the Grid Portal / Status Overview / Node Status page.
"""

WARNING_TRIPPOINT = 70
ERROR_TRIPPOINT = 90


def action():
    results = []
    rc, out = j.sal.process.execute("ipmitool sdr type 'Temp'", die=False)
    if rc == 0:
        if out:
            # SAMPLE:
            # root@du-conv-3-01:~# ipmitool sdr type "Temp"
            # Temp             | 0Eh | ok  |  3.1 | 37 degrees C
            # Temp             | 0Fh | ok  |  3.2 | 34 degrees C
            # Inlet Temp       | B1h | ok  | 64.96 | 28 degrees C
            # Exhaust Temp     | B2h | ns  | 144.96 | Disabled

            for line in out.splitlines():
                if "|" in line:
                    parts = [part.strip() for part in line.split("|")]
                    id_, sensorstatus, message = parts[0], parts[2], parts[-1]

                    if sensorstatus == "ns" and "no reading" in message.lower():
                        continue

                    if sensorstatus != "ok" and "no reading" not in message.lower():
                        result = get_results(resource=id_, status='WARNING', message=message)
                        results.append(result)
                        continue
                    result = get_results(resource=id_, status=sensorstatus, message=message)
                    results.append(result)
    else:
        result = get_results(status="SKIPPED", message="NO temp information available")
        results.append(result)

    return results


def get_results(resource=None, status='OK', message='', temperature=0):
    result = {
        "status": status.upper(),
        "message": "%s: %s" % (resource, message),
        "name": resource,
        "category": "Hardware",
        "id": "Temperature",
    }
    if status != "OK":
        return result

    if temperature >= WARNING_TRIPPOINT:
        result["status"] = "WARNING"
    elif temperature >= ERROR_TRIPPOINT:
        result["status"] = "ERROR"
    return result


if __name__ == '__main__':
    import json
    print(json.dumps(action()))
