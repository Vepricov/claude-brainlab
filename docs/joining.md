# Joining the lab's knowledge base

The base is a shared, typed record of what the lab claims, ran, measured and decided, plus a
library of read papers. Your agents read it and write to it over MCP; you set it up once.

## What a lead does, once per person

    python3 invite.py --email name@brainlab-ai.com

That creates the member in the base and prints a one-time link. Hand it over the way you would
hand over a password: it works once, and there is no self-registration. There is no password reset
either — a lost password means a new invite, which is one fewer path an attacker can walk.

## What you do, once

1. Open the link, choose a password of at least twelve characters. You are now logged in.
2. Type the name of the machine or agent you are setting up — `laptop`, `server-run`,
   `codex` — and press **Выдать токен**.
3. Copy the token. It is shown once: the base keeps only its fingerprint.
4. Paste the block the page shows into your MCP client, or run the one command below.

        python3 scripts/lab_connect.py --token <your token> --agent laptop

Repeat step 2 for every agent you run. One token per agent is the point: the journal then shows
which of your agents wrote a record, and a stolen laptop costs you one token rather than your
whole account.

## What you can do from the first minute

- **Read everything.** Search covers the lab's own records and the library at once. Ask
  `search_lab` a question in plain words; it walks the graph, so a claim arrives with the run that
  tested it and the number that came out.
- **Write to your own project.** Membership is per project: your project is yours, everything else
  is read-only until someone adds you.

## What the base will refuse, and why

- A hypothesis without a falsifier that can actually happen. "Worse in every setting" never
  arrives, so it closes nothing.
- Evidence without a number in `metrics`. A measurement nobody can compare is not a measurement.
- A claim about a paper without a verbatim quote from that paper's stored text.
- A fragment instead of a statement: a table row, half a formula, an item from a numbered list.

These are not style rules. Every one of them exists because a record that breaks it cannot be
cited by anyone but its author.

## When something goes wrong

The refusal names the defect and what to do about it — read it rather than retrying. If the
service itself does not answer, tell the lead: it runs as a single process, and a watchdog
restarts it, but a wedge is worth knowing about.
