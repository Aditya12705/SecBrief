import httpx
from typing import List, Dict, Optional

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL = "https://osv.dev/vulnerability/{id}"

async def scan_packages_osv(packages: List[Dict]) -> Dict:
    """
    packages: list of {"name": str, "version": str, "ecosystem": str}
    Returns structured vulnerability results.
    """
    queries = [
        {
            "version": pkg["version"],
            "package": {"name": pkg["name"], "ecosystem": pkg["ecosystem"]}
        }
        for pkg in packages
    ]

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(OSV_BATCH_URL, json={"queries": queries})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return {"error": str(e), "vulnerabilities": [], "packages_scanned": len(packages)}

    results = data.get("results", [])
    vulnerabilities = []

    for i, result in enumerate(results):
        pkg = packages[i] if i < len(packages) else {}
        for vuln in result.get("vulns", []):
            severity = "UNKNOWN"
            cvss_score = None
            # Try to get severity from database_specific or severity array
            for sev in vuln.get("severity", []):
                if sev.get("type") in ("CVSS_V3", "CVSS_V2"):
                    cvss_score = sev.get("score")
                    break
            db_specific = vuln.get("database_specific", {})
            severity = db_specific.get("severity", severity)
            if not severity or severity == "UNKNOWN":
                if cvss_score:
                    try:
                        score = float(cvss_score.split("/")[0]) if "/" in str(cvss_score) else float(cvss_score)
                        if score >= 9.0: severity = "CRITICAL"
                        elif score >= 7.0: severity = "HIGH"
                        elif score >= 4.0: severity = "MEDIUM"
                        else: severity = "LOW"
                    except: pass

            vulnerabilities.append({
                "package": pkg.get("name", "unknown"),
                "version": pkg.get("version", "unknown"),
                "ecosystem": pkg.get("ecosystem", "unknown"),
                "vuln_id": vuln.get("id", ""),
                "summary": vuln.get("summary", "No summary available"),
                "severity": severity,
                "cvss_score": cvss_score,
                "osv_url": OSV_VULN_URL.format(id=vuln.get("id", "")),
                "aliases": vuln.get("aliases", []),
                "published": vuln.get("published", ""),
            })

    return {
        "packages_scanned": len(packages),
        "vulnerabilities": vulnerabilities,
        "critical_count": sum(1 for v in vulnerabilities if v["severity"] == "CRITICAL"),
        "high_count": sum(1 for v in vulnerabilities if v["severity"] == "HIGH"),
        "medium_count": sum(1 for v in vulnerabilities if v["severity"] == "MEDIUM"),
        "low_count": sum(1 for v in vulnerabilities if v["severity"] == "LOW"),
        "total_vulns": len(vulnerabilities),
    }

async def scan_container_osv(image: str, sbom_packages: Optional[List[Dict]] = None) -> Dict:
    """
    image: Docker image string like "nginx:1.21" or "python:3.9-alpine"
    sbom_packages: optional list of {"name": str, "version": str, "ecosystem": str}
    """
    # Parse image name and tag
    if ":" in image:
        img_name, tag = image.rsplit(":", 1)
    else:
        img_name, tag = image, "latest"

    # Guess base OS ecosystem from image name/tag
    base_os = "unknown"
    ecosystem_guess = None
    name_lower = img_name.lower()
    tag_lower = tag.lower()

    if "alpine" in name_lower or "alpine" in tag_lower:
        base_os = "Alpine Linux"
        ecosystem_guess = "Alpine"
    elif "debian" in name_lower or "debian" in tag_lower or "buster" in tag_lower or "bullseye" in tag_lower or "bookworm" in tag_lower:
        base_os = "Debian"
        ecosystem_guess = "Debian"
    elif "ubuntu" in name_lower or "ubuntu" in tag_lower or "focal" in tag_lower or "jammy" in tag_lower:
        base_os = "Ubuntu"
        ecosystem_guess = "Ubuntu"
    elif any(x in name_lower for x in ["python", "node", "ruby", "golang", "openjdk", "php"]):
        base_os = f"{img_name.split('/')[-1].capitalize()} (likely Debian/Ubuntu)"
        ecosystem_guess = "Debian"
    elif "scratch" in name_lower or "distroless" in name_lower:
        base_os = "Distroless/Scratch"
        ecosystem_guess = None
    else:
        base_os = "Unknown (assuming Debian-based)"
        ecosystem_guess = "Debian"

    # Use sbom_packages if provided, else return metadata-only scan
    packages_to_scan = sbom_packages or []
    osv_result = {"packages_scanned": 0, "vulnerabilities": [], "total_vulns": 0,
                  "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0}

    if packages_to_scan:
        osv_result = await scan_packages_osv(packages_to_scan)

    return {
        "image": img_name,
        "tag": tag,
        "full_image": image,
        "base_os_guess": base_os,
        "ecosystem_guess": ecosystem_guess,
        **osv_result,
    }
