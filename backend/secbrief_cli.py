#!/usr/bin/env python3
import argparse, json, os, sys, requests
import re
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),"../.env"), override=True)
except ImportError:
    pass # Fallback to existing environment variables
API = os.getenv("NEXT_PUBLIC_API_URL","http://localhost:8000")
R="\033[91m";Y="\033[93m";G="\033[92m";B="\033[94m";GR="\033[90m";RST="\033[0m";BD="\033[1m"
SC={"CRITICAL":R,"HIGH":Y,"MEDIUM":B,"LOW":G,"NONE":GR,"UNKNOWN":GR}
def col(t,s): return f"{SC.get(s,'')}{t}{RST}"
def banner(): print(f"\n{BD}╔══════════════════════════╗\n║  SecBrief CLI v1.0.0     ║\n║  Mistral + ArmorIQ       ║\n╚══════════════════════════╝{RST}\n")

def discover_packages(root_dir):
    """
    Walk the directory tree from root_dir and extract all packages from:
    - package.json (npm)
    - requirements.txt (PyPI)
    - go.mod (Go)
    - pom.xml (Maven)
    - Gemfile.lock (RubyGems)
    - Pipfile (PyPI)
    - poetry.lock (PyPI)
    - yarn.lock (npm)
    Returns: list of {"ecosystem": str, "packages": [{"name": str, "version": str}], "source_file": str}
    """
    results = []
    root = Path(root_dir).resolve()

    # ── npm: package.json ──
    for fpath in root.rglob("package.json"):
        if "node_modules" in fpath.parts:
            continue
        try:
            import json as _json
            data = _json.loads(fpath.read_text(encoding="utf-8", errors="ignore"))
            pkgs = []
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                for name, ver in data.get(section, {}).items():
                    # Strip semver operators: ^1.0.0 -> 1.0.0
                    clean_ver = re.sub(r'^[\^~>=<*]+ *', '', str(ver)).split(" ")[0] or "latest"
                    pkgs.append({"name": name, "version": clean_ver})
            if pkgs:
                results.append({"ecosystem": "npm", "packages": pkgs[:30], "source_file": str(fpath.relative_to(root))})
        except: pass

    # ── PyPI: requirements.txt ──
    for fpath in root.rglob("requirements*.txt"):
        try:
            pkgs = []
            for line in fpath.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # Handle: Django==3.2.0, flask>=2.0, requests
                m = re.match(r'^([A-Za-z0-9_\-\.]+)\s*[=><!\^~]+\s*([A-Za-z0-9_\.\-]+)', line)
                if m:
                    pkgs.append({"name": m.group(1), "version": m.group(2)})
                else:
                    name = re.split(r'[=><!\s\[;]', line)[0].strip()
                    if name:
                        pkgs.append({"name": name, "version": "latest"})
            if pkgs:
                results.append({"ecosystem": "PyPI", "packages": pkgs[:30], "source_file": str(fpath.relative_to(root))})
        except: pass

    # ── PyPI: Pipfile ──
    for fpath in root.rglob("Pipfile"):
        try:
            pkgs = []
            in_packages = False
            for line in fpath.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line in ("[packages]", "[dev-packages]"):
                    in_packages = True; continue
                if line.startswith("["):
                    in_packages = False; continue
                if in_packages and "=" in line:
                    parts = line.split("=", 1)
                    name = parts[0].strip().strip('"')
                    ver = parts[1].strip().strip('"').lstrip("=><^~* ")
                    if name and not name.startswith("#"):
                        pkgs.append({"name": name, "version": ver or "latest"})
            if pkgs:
                results.append({"ecosystem": "PyPI", "packages": pkgs[:30], "source_file": str(fpath.relative_to(root))})
        except: pass

    # ── Go: go.mod ──
    for fpath in root.rglob("go.mod"):
        try:
            pkgs = []
            in_require = False
            for line in fpath.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("require ("):
                    in_require = True; continue
                if in_require and line == ")":
                    in_require = False; continue
                if in_require or line.startswith("require "):
                    line = line.replace("require ", "").strip()
                    parts = line.split()
                    if len(parts) >= 2 and not parts[0].startswith("//"):
                        pkgs.append({"name": parts[0], "version": parts[1].lstrip("v")})
            if pkgs:
                results.append({"ecosystem": "Go", "packages": pkgs[:30], "source_file": str(fpath.relative_to(root))})
        except: pass

    # ── Maven: pom.xml ──
    for fpath in root.rglob("pom.xml"):
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            deps = re.findall(r'<dependency>.*?</dependency>', text, re.DOTALL)
            pkgs = []
            for dep in deps:
                gid = re.search(r'<groupId>(.*?)</groupId>', dep)
                aid = re.search(r'<artifactId>(.*?)</artifactId>', dep)
                ver = re.search(r'<version>(.*?)</version>', dep)
                if gid and aid:
                    name = f"{gid.group(1)}:{aid.group(1)}"
                    version = ver.group(1) if ver else "latest"
                    if not version.startswith("$"):
                        pkgs.append({"name": name, "version": version})
            if pkgs:
                results.append({"ecosystem": "Maven", "packages": pkgs[:30], "source_file": str(fpath.relative_to(root))})
        except: pass

    # ── Ruby: Gemfile.lock ──
    for fpath in root.rglob("Gemfile.lock"):
        try:
            pkgs = []
            in_specs = False
            for line in fpath.read_text(encoding="utf-8", errors="ignore").splitlines():
                if "    specs:" in line:
                    in_specs = True; continue
                if in_specs:
                    m = re.match(r'      ([a-zA-Z0-9_\-]+) \(([^\)]+)\)', line)
                    if m:
                        pkgs.append({"name": m.group(1), "version": m.group(2)})
                    elif not line.strip():
                        in_specs = False
            if pkgs:
                results.append({"ecosystem": "RubyGems", "packages": pkgs[:30], "source_file": str(fpath.relative_to(root))})
        except: pass

    return results


def discover_dockerfile(root_dir):
    """
    Find Dockerfile(s) in the project and extract:
    - Base image (FROM line)
    - Any packages installed via RUN pip install / npm install / apt-get install
    Returns: list of {"dockerfile": str, "image": str, "sbom_packages": [...]}
    """
    results = []
    root = Path(root_dir).resolve()

    for fpath in list(root.rglob("Dockerfile")) + list(root.rglob("Dockerfile.*")):
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()

            # Extract base image from first FROM
            image = "unknown:latest"
            for line in lines:
                line = line.strip()
                if line.upper().startswith("FROM") and "scratch" not in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        img = parts[1]
                        # ignore build args like ${BASE_IMAGE}
                        if not img.startswith("$"):
                            image = img
                    break

            # Extract packages from RUN commands
            sbom = []
            full_text = " ".join(lines)

            # pip install
            pip_pkgs = re.findall(r'pip[23]?\s+install\s+([^\\\n&;]+)', full_text)
            for pkg_str in pip_pkgs:
                for pkg in pkg_str.split():
                    pkg = pkg.strip().strip("'\"\\")
                    if pkg.startswith("-") or not pkg: continue
                    m = re.match(r'^([A-Za-z0-9_\-\.]+)[=><!\^~]+([A-Za-z0-9_\.\-]+)', pkg)
                    if m:
                        sbom.append({"name": m.group(1), "version": m.group(2), "ecosystem": "PyPI"})
                    elif re.match(r'^[A-Za-z]', pkg):
                        sbom.append({"name": pkg, "version": "latest", "ecosystem": "PyPI"})

            # npm install
            npm_pkgs = re.findall(r'npm\s+install\s+([^\\\n&;]+)', full_text)
            for pkg_str in npm_pkgs:
                for pkg in pkg_str.split():
                    pkg = pkg.strip().strip("'\"\\")
                    if pkg.startswith("-") or not pkg: continue
                    if "@" in pkg and not pkg.startswith("@"):
                        n, v = pkg.rsplit("@", 1)
                        sbom.append({"name": n, "version": v, "ecosystem": "npm"})
                    elif re.match(r'^[A-Za-z@]', pkg):
                        sbom.append({"name": pkg, "version": "latest", "ecosystem": "npm"})

            # apt-get install (flag OS packages)
            apt_pkgs = re.findall(r'apt(?:-get)?\s+install\s+(?:-y\s+)?([^\\\n&;]+)', full_text)
            for pkg_str in apt_pkgs:
                for pkg in pkg_str.split():
                    pkg = pkg.strip().strip("'\"\\")
                    if pkg.startswith("-") or not pkg or len(pkg) < 2: continue
                    sbom.append({"name": pkg, "version": "latest", "ecosystem": "Debian"})

            results.append({
                "dockerfile": str(fpath.relative_to(root)),
                "image": image,
                "sbom_packages": sbom[:20]
            })
        except: pass

    return results
def armoriq_block(a):
    if not a: return
    s=a.get("status",""); print(f"\n{BD}━━ ArmorIQ ━━{RST}")
    print(f"  Status : {G+'✅ ENFORCED' if s=='enforced' else Y+'📋 RECEIPT' if s=='receipt_only' else Y+'⚠️ UNAVAILABLE' if s=='unavailable' else GR+'Skipped'}{RST}")
    if a.get("receipt"): print(f"  Receipt: {GR}{str(a['receipt'])[:64]}...{RST}")
    for e in a.get("enforcement",[]):
        if isinstance(e,dict) and e.get("decision")=="BLOCK":
            print(f"  {R}{BD}🚫 BLOCKED: {e.get('action')} on {e.get('resource')}{RST}")
def parse_pkgs(s):
    out=[]
    for raw in s.split(","):
        t=raw.strip()
        if t.startswith("@"): rest=t[1:]; i=rest.rfind("@"); out.append({"name":"@"+rest[:i],"version":rest[i+1:]} if i>-1 else {"name":t,"version":"latest"})
        else: i=t.rfind("@"); out.append({"name":t[:i],"version":t[i+1:]} if i>-1 else {"name":t,"version":"latest"})
    return out
def table(findings, cols):
    if not findings: print(f"\n{G}✅ No vulnerabilities found.{RST}\n"); return
    W={"package":24,"version":10,"severity":10,"cve_ids":22,"summary":50,"component":24,"recommended_version":12}
    print("\n"+BD+"  ".join(f"{c.upper():<{W.get(c,15)}}" for c in cols)+RST); print("─"*100)
    for f in findings:
        sev=f.get("severity","UNKNOWN"); parts=[]
        for c in cols:
            v=f.get(c,""); v=", ".join(v) if isinstance(v,list) else str(v or "—"); w=W.get(c,15)
            parts.append(f"{col(sev,sev):<{w+len(SC.get(sev,''))+4}}" if c=="severity" else f"{v[:w]:<{w}}")
        print("  ".join(parts))
    print()
def cmd_pkg(args,j):
    pkgs=parse_pkgs(args.packages)
    try: r=requests.post(f"{API}/api/package-scan",json={"ecosystem":args.ecosystem,"packages":pkgs},timeout=60); r.raise_for_status(); d=r.json()
    except Exception as e: print(f"{R}{e}{RST}"); sys.exit(1)
    if j: print(json.dumps(d,indent=2)); sys.exit(1 if d.get("critical_count",0)>0 else 0)
    print(f"  Ecosystem: {BD}{args.ecosystem}{RST}\n  {col('CRITICAL','CRITICAL')}: {d.get('critical_count',0)}  {col('HIGH','HIGH')}: {d.get('high_count',0)}  MEDIUM: {d.get('medium_count',0)}  LOW: {d.get('low_count',0)}")
    table([f for f in d.get("findings",[]) if f.get("severity")!="NONE"],["package","version","severity","cve_ids","summary","recommended_version"])
    armoriq_block(d.get("armoriq")); sys.exit(1 if d.get("critical_count",0)>0 else 0)
def cmd_con(args,j):
    sbom=[]
    if getattr(args,"sbom",None):
        for e in args.sbom.split(","):
            t=e.strip(); ci=t.rfind(":"); ai=t.rfind("@")
            if ci>ai>-1: sbom.append({"name":t[:ai],"version":t[ai+1:ci],"ecosystem":t[ci+1:]})
    try: r=requests.post(f"{API}/api/container-scan",json={"image":args.image,"sbom_packages":sbom or None},timeout=60); r.raise_for_status(); d=r.json()
    except Exception as e: print(f"{R}{e}{RST}"); sys.exit(1)
    if j: print(json.dumps(d,indent=2)); sys.exit(1 if d.get("critical_count",0)>0 else 0)
    print(f"  Image: {BD}{args.image}{RST}  OS: {d.get('base_os_guess','?')}  Risk: {col(d.get('overall_risk','?'),d.get('overall_risk','?'))}")
    if d.get("uses_latest_tag"): print(f"  {Y}⚠️  Pin to a specific digest — 'latest' is insecure{RST}")
    table(d.get("image_findings",[])+d.get("package_findings",[]),["component","severity","cve_ids","summary"])
    if d.get("hardening_steps"): print(f"{BD}🔧 Hardening:{RST}"); [print(f"  • {s}") for s in d["hardening_steps"]]; print()
    armoriq_block(d.get("armoriq")); sys.exit(1 if d.get("critical_count",0)>0 else 0)
def cmd_history(_args,j):
    _ = _args
    try: r=requests.get(f"{API}/api/scan-history",timeout=15); r.raise_for_status(); d=r.json()
    except Exception as e: print(f"{R}{e}{RST}"); sys.exit(1)
    if j: print(json.dumps(d,indent=2)); return
    logs=d.get("logs",[])
    if not logs: print(f"{GR}No history.{RST}"); return
    print(f"\n{BD}{'Timestamp':<22}{'Type':<12}{'Target':<28}{'Vulns':<8}{'Crit':<6}Receipt{RST}")
    print("─"*90)
    for l in logs: print(f"{str(l.get('timestamp',''))[:21]:<22}{l.get('scan_type',''):<12}{str(l.get('target',''))[:27]:<28}{l.get('vulns_found',0):<8}{l.get('critical_count',0):<6}{str(l.get('armoriq_receipt',''))[:30]}")
def cmd_scan_project(args, j):
    root = getattr(args, "path", ".") or "."
    print(f"  {BD}Scanning project at: {os.path.abspath(root)}{RST}")
    print(f"  Discovering dependency files...\n")

    discoveries = discover_packages(root)

    if not discoveries:
        print(f"{Y}⚠️  No dependency files found (package.json, requirements.txt, go.mod, pom.xml, Gemfile.lock){RST}")
        sys.exit(0)

    all_results = []
    total_critical = 0
    total_high = 0
    total_vulns = 0

    for disc in discoveries:
        eco = disc["ecosystem"]
        pkgs = disc["packages"]
        src = disc["source_file"]
        print(f"{BD}━━ {eco} — {src} ({len(pkgs)} packages) ━━{RST}")

        try:
            r = requests.post(f"{API}/api/package-scan",
                json={"ecosystem": eco, "packages": pkgs},
                timeout=90)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  {R}Error scanning {src}: {e}{RST}\n"); continue

        if j:
            all_results.append({"source": src, "ecosystem": eco, **data})
        else:
            print(f"  Packages: {len(pkgs)}  {col('CRITICAL','CRITICAL')}: {data.get('critical_count',0)}  {col('HIGH','HIGH')}: {data.get('high_count',0)}  MEDIUM: {data.get('medium_count',0)}  LOW: {data.get('low_count',0)}")
            findings = [f for f in data.get("findings", []) if f.get("severity") not in ("NONE", None)]
            table(findings, ["package", "version", "severity", "cve_ids", "summary", "recommended_version"])
            armoriq_block(data.get("armoriq"))

        total_critical += data.get("critical_count", 0)
        total_high += data.get("high_count", 0)
        total_vulns += data.get("total_scanned", len(pkgs))

    if j:
        print(json.dumps({"project": root, "scans": all_results}, indent=2))
        sys.exit(1 if total_critical > 0 else 0)

    print(f"\n{BD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"PROJECT SCAN SUMMARY")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RST}")
    print(f"  Files scanned : {len(discoveries)}")
    print(f"  Total packages: {total_vulns}")
    print(f"  {col('CRITICAL','CRITICAL')}: {total_critical}   {col('HIGH','HIGH')}: {total_high}")
    if total_critical > 0:
        print(f"\n  {R}{BD}❌ FAILED — Critical vulnerabilities found. Fix before deploying.{RST}")
    elif total_high > 0:
        print(f"\n  {Y}⚠️  WARNING — High severity issues found.{RST}")
    else:
        print(f"\n  {G}✅ PASSED — No critical/high vulnerabilities.{RST}")
    sys.exit(1 if total_critical > 0 else 0)


def cmd_scan_dockerfile(args, j):
    root = getattr(args, "path", ".") or "."
    print(f"  {BD}Scanning Dockerfiles at: {os.path.abspath(root)}{RST}\n")

    dockerfiles = discover_dockerfile(root)

    if not dockerfiles:
        print(f"{Y}⚠️  No Dockerfile found in {root}{RST}")
        sys.exit(0)

    all_results = []
    total_critical = 0
    total_high = 0

    for df in dockerfiles:
        print(f"{BD}━━ {df['dockerfile']} — base image: {df['image']} ({len(df['sbom_packages'])} extracted packages) ━━{RST}")

        try:
            r = requests.post(f"{API}/api/container-scan",
                json={"image": df["image"], "sbom_packages": df["sbom_packages"] or None},
                timeout=90)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  {R}Error: {e}{RST}\n"); continue

        if j:
            all_results.append({"dockerfile": df["dockerfile"], **data})
        else:
            print(f"  Base OS   : {data.get('base_os_guess','?')}")
            print(f"  Risk      : {col(data.get('overall_risk','?'), data.get('overall_risk','?'))}")
            if data.get("uses_latest_tag"):
                print(f"  {Y}⚠️  'latest' tag detected — pin to a digest{RST}")
            print(f"  {col('CRITICAL','CRITICAL')}: {data.get('critical_count',0)}   {col('HIGH','HIGH')}: {data.get('high_count',0)}   MEDIUM: {data.get('medium_count',0)}   LOW: {data.get('low_count',0)}")
            all_f = data.get("image_findings", []) + data.get("package_findings", [])
            table(all_f, ["component", "severity", "cve_ids", "summary"])
            if data.get("hardening_steps"):
                print(f"{BD}🔧 Hardening:{RST}")
                for s in data["hardening_steps"]: print(f"  • {s}")
                print()
            armoriq_block(data.get("armoriq"))

        total_critical += data.get("critical_count", 0)
        total_high += data.get("high_count", 0)

    if j:
        print(json.dumps({"project": root, "dockerfiles": all_results}, indent=2))
        sys.exit(1 if total_critical > 0 else 0)

    print(f"\n{BD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"DOCKERFILE SCAN SUMMARY")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RST}")
    print(f"  Dockerfiles : {len(dockerfiles)}")
    print(f"  {col('CRITICAL','CRITICAL')}: {total_critical}   {col('HIGH','HIGH')}: {total_high}")
    if total_critical > 0:
        print(f"\n  {R}{BD}❌ FAILED — Critical container vulnerabilities found.{RST}")
    else:
        print(f"\n  {G}✅ PASSED{RST}")
    sys.exit(1 if total_critical > 0 else 0)
def cmd_scan_repo(args, j):
    root = getattr(args, "path", ".") or "."
    print(f"  {BD}Full repository scan at: {os.path.abspath(root)}{RST}\n")

    try:
        r = requests.post(f"{API}/api/project-scan", json={"path": root}, timeout=180)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"{R}{e}{RST}")
        sys.exit(1)

    if j:
        print(json.dumps(data, indent=2))
        sys.exit(1 if data.get("critical_count", 0) > 0 else 0)

    print(f"{BD}Target:{RST} {data.get('target','')}")
    if data.get("summary"):
        print(f"\n{BD}Summary:{RST}\n{data.get('summary')}\n")

    print(f"  {col('CRITICAL','CRITICAL')}: {data.get('critical_count',0)}   {col('HIGH','HIGH')}: {data.get('high_count',0)}   MEDIUM: {data.get('medium_count',0)}   LOW: {data.get('low_count',0)}")

    dep = [f for f in data.get("dependency_findings", []) if f.get("severity") not in ("NONE", None)]
    if dep:
        print(f"\n{BD}━━ Dependency Findings ━━{RST}")
        table(dep, ["package", "version", "severity", "cve_ids", "summary", "recommended_version"])

    code = data.get("code_findings", []) or []
    if code:
        print(f"\n{BD}━━ Code Findings ━━{RST}")
        table(code, ["file", "line", "severity", "summary"])

    cfg = data.get("config_findings", []) or []
    if cfg:
        print(f"\n{BD}━━ Config Findings ━━{RST}")
        table(cfg, ["file", "severity", "summary"])

    armoriq_block(data.get("armoriq"))
    sys.exit(1 if data.get("critical_count", 0) > 0 else 0)

def main():
    p=argparse.ArgumentParser(prog="secbrief")
    p.add_argument("--version",action="version",version="SecBrief CLI v1.0.0")
    p.add_argument("--output",choices=["json","table"],default="table")
    sub=p.add_subparsers(dest="cmd")
    sp=sub.add_parser("scan-packages"); sp.add_argument("--ecosystem",required=True); sp.add_argument("--packages",required=True)
    sc=sub.add_parser("scan-container"); sc.add_argument("--image",required=True); sc.add_argument("--sbom",default=None)
    sub.add_parser("scan-history")
    sp2 = sub.add_parser("scan-project", help="Auto-scan entire project for vulnerable dependencies")
    sp2.add_argument("--path", default=".", help="Path to project root (default: current directory)")
    sp3 = sub.add_parser("scan-dockerfile", help="Auto-scan Dockerfile(s) for base image and package CVEs")
    sp3.add_argument("--path", default=".", help="Path to search for Dockerfiles (default: current directory)")
    sp4 = sub.add_parser("scan-repo", help="Scan entire repository (deps + code + configs)")
    sp4.add_argument("--path", default=".", help="Path to repo root (default: current directory)")
    argv = sys.argv[1:]
    subcommands = {"scan-packages", "scan-container", "scan-history", "scan-project", "scan-dockerfile", "scan-repo"}
    cmd_index = None
    for idx, tok in enumerate(argv):
        if tok in subcommands:
            cmd_index = idx
            break
    if cmd_index is not None and "--output" in argv:
        oi = argv.index("--output")
        if oi > cmd_index and oi + 1 < len(argv):
            opt = argv[oi : oi + 2]
            del argv[oi : oi + 2]
            argv = opt + argv

    args=p.parse_args(argv); j=args.output=="json"
    if not j: banner()
    if args.cmd=="scan-packages": cmd_pkg(args,j)
    elif args.cmd=="scan-container": cmd_con(args,j)
    elif args.cmd=="scan-history": cmd_history(args,j)
    elif args.cmd == "scan-project": cmd_scan_project(args, j)
    elif args.cmd == "scan-dockerfile": cmd_scan_dockerfile(args, j)
    elif args.cmd == "scan-repo": cmd_scan_repo(args, j)
    else: p.print_help()
if __name__=="__main__": main()
