# Public-content review

The repository is designed to distribute a reusable foundation. Public content
must be deliberately selected; copying a personal environment and deleting a few
obvious files is not a reliable publication process.

Allowed content includes the shared concept definitions, neutral templates,
generic procedures, code, tests using invented data, and deployment documentation.
The public file manifest in `scripts/check_public.py` lists every distributable
file. Adding a file requires an explicit manifest change and review.

Keep personal identity seeds, experiential archives, correspondence, source chat
logs, photographs, OCR output, embeddings of personal text, backups, access
diagnostics, and provider account configuration out of this repository. This
includes private record keys and links that reveal the structure of an archive.
Anonymizing a name alone does not make a personal experience public material.

Before a commit or publication:

1. Inspect the full candidate file list and diff. Review new files as carefully
   as changes to tracked files. Check staged content independently of worktree
   edits. Avoid indiscriminate staging from a directory containing private data.
2. Run the tests and `python3 scripts/check_public.py`. The checker examines
   publishable worktree files and the Git index, enforces the explicit manifest,
   and flags selected secret and local-path patterns without printing matched
   values. It also verifies the concept data and its rendered documentation.
3. Review meaning as well as patterns: provenance, permission to distribute,
   factual claims, and third-party attribution. Automated checks cannot recognize
   every personal story or secret.
4. Inspect the outgoing commits. If sensitive material entered an earlier commit,
   removing it from the latest file does not remove it from Git history. Stop
   publication and assess the affected history and credentials first.
5. Confirm the published result contains only the reviewed changes. A passing
   local scan does not establish what was pushed or deployed.

Generated instances belong outside the public checkout. Their `.gitignore` ignores
everything as a convenience, not a security boundary. Git ignore rules do not
protect an already tracked file or prevent force-adding a file.
