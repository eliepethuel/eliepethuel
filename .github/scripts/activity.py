"""Met à jour la section « Activité récente » du README à partir des événements publics GitHub."""
import json
import os
import re
import urllib.request

USER = os.environ["GH_USERNAME"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_LINES = 6
START, END = "<!--START_SECTION:activity-->", "<!--END_SECTION:activity-->"


def fetch_events():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/events/public?per_page=100",
        headers={"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def describe(event):
    repo = event["repo"]["name"]
    link = f"[{repo.split('/')[-1]}](https://github.com/{repo})"
    payload = event.get("payload", {})
    kind = event["type"]
    if kind == "PushEvent":
        return f"⬆️ A poussé du code sur {link}"
    if kind == "CreateEvent":
        if payload.get("ref_type") == "repository":
            return f"🆕 A créé le dépôt {link}"
        if payload.get("ref_type") == "branch":
            return f"🌿 A créé la branche `{payload.get('ref')}` sur {link}"
        return None
    if kind == "PullRequestEvent":
        pr = payload.get("pull_request", {})
        action = "fusionné" if pr.get("merged") else {"opened": "ouvert", "closed": "fermé"}.get(payload.get("action"))
        if action:
            return f"🔀 A {action} la PR [#{pr.get('number')}]({pr.get('html_url')}) sur {link}"
    if kind == "IssuesEvent" and payload.get("action") in ("opened", "closed"):
        issue = payload["issue"]
        verb = "ouvert" if payload["action"] == "opened" else "fermé"
        return f"❗ A {verb} l'issue [#{issue['number']}]({issue['html_url']}) sur {link}"
    if kind == "ReleaseEvent":
        return f"🚀 A publié la version `{payload['release']['tag_name']}` de {link}"
    if kind == "ForkEvent":
        return f"🍴 A forké {link}"
    if kind == "WatchEvent":
        return f"⭐ A mis une étoile à {link}"
    return None


def main():
    lines = []
    for event in fetch_events():
        if event["repo"]["name"].lower() == f"{USER}/{USER}".lower():
            continue  # ignore les commits automatiques du dépôt de profil
        line = describe(event)
        if line and line not in lines:
            lines.append(line)
        if len(lines) == MAX_LINES:
            break

    block = "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1)) or "_Pas d'activité publique récente._"
    with open("README.md", encoding="utf-8") as f:
        readme = f.read()
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: f"{START}\n{block}\n{END}",
        readme,
        flags=re.S,
    )
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)


if __name__ == "__main__":
    main()
