window.SYSTEM_EXAMPLES = {
  verified: "09-09-2026",
  surfaces: {
    obsidian: {
      number: "P1",
      title: "Obsidian",
      kicker: "Personal research memory",
      promise: "A place for detailed understanding, drafts, a research log, and private project context.",
      owns: ["Full reading notes and meeting notes", "Draft reasoning and plans", "The project hub, experiment log, and links to result files"],
      doesNotOwn: ["Shared scientific records for the lab", "Team tasks", "An agent's automatic session history"],
      path: ["Working material emerges in the project", "The researcher turns it into a readable note", "Only the explicitly selected material is shown to the owner before publication", "Once approved, it is published to Lab Knowledge as a typed record"],
      routes: [{kind:"Workflow", title:"Projects and memory", text:"How to set up a project, where its hub lives, and what can be published.", process:"projects", tool:"obsidian-project-bootstrap"}],
      links: [{label:"Obsidian", url:"https://obsidian.md/"}, {label:"Skill: project memory", url:"https://github.com/Vepricov/claude-brainlab/tree/main/skills/obsidian-project-memory"}]
    },
    mempalace: {
      number: "P2",
      title: "MemPalace",
      kicker: "Long-term agent memory",
      promise: "Recovers past decisions, work history, and context across sessions so the agent can resume a task with an understanding of prior work.",
      owns: ["Past work episodes and their provenance", "Connections between tasks, decisions, and projects", "Context that helps restore a session"],
      doesNotOwn: ["Scientific evidence", "Current server status without a live check", "A person's private notes"],
      path: ["The agent first searches for relevant history", "It retrieves episodes together with their provenance", "It rechecks changeable facts in the live system", "It uses memory as context, not as evidence"],
      routes: [{kind:"Workflow", title:"Agent orchestration", text:"See how context reaches Jarvis, Hermes, and project watchers.", process:"experiments", tool:"watcher"}],
      links: [{label:"MemPalace on GitHub", url:"https://github.com/MemPalace/mempalace"}]
    },
    yonote: {
      number: "P3",
      title: "Yonote",
      kicker: "Project overview and coordination",
      promise: "Provides a readable project page and its working task board without duplicating the scientific database.",
      owns: ["One readable project page", "Project task board: CODE · Tasks", "CODE · Meetings and documents, with CODE · Meeting DD-MM-YYYY notes"],
      facts: ["5 live collections", "21 projects in the manifest", "20 page + Kanban bindings", "13 bindings with explicit view IDs", "op-lora is not yet bound"],
      doesNotOwn: ["Full provenance of scientific claims", "Raw logs and private notes", "A second writable copy of hypotheses and evidence"],
      path: ["The team and verified paper materials", "A brief project description and its audience", "The current stage, main hypotheses, and supported results", "Evidence limitations and a link to the project's single CODE task board"],
      routes: [
        {kind:"Project page", title:"Yonote project view", text:"The structure and scope of a readable project overview.", process:"projects", tool:"yonote-project-view"},
        {kind:"Task board", title:"Yonote task broker", text:"Tasks, owners, dates assigned, statuses, and safe writes.", process:"projects", tool:"yonote-task-broker"},
        {kind:"Meeting documents", title:"Yonote call documents", text:"A brief approved meeting summary, separate from task rows.", process:"calls", tool:"yonote-call"}
      ],
      links: [{label:"BRAIn Lab in Yonote", url:"https://brain-lab.yonote.ru/"}]
    }
  },
  liveMcp: {
    title: "Lab Knowledge MCP on brain_lab",
    subtitle: "A verified snapshot of the running service. This is a read-only overview, not an administration panel.",
    verifiedAt: "09-09-2026",
    deployment: {host:"brain_lab", service:"lab-knowledge-user.service", endpoint:"127.0.0.1:8001 through a private connection", revision:"The deployed source code was checked separately", state:"Running · schema version 34 · 58 MCP tools"},
    counts: [
      {value:"47", label:"projects and topics"}, {value:"714", label:"claims"}, {value:"729", label:"runs"},
      {value:"894", label:"measurements"}, {value:"153", label:"derivations · 145 complete"}, {value:"345", label:"rules"},
      {value:"551", label:"paper"}, {value:"4 231", label:"paper sections"}, {value:"9 265", label:"paper claims · 9,056 quotations verified"},
      {value:"116", label:"paper links"}, {value:"547", label:"journal entries"}, {value:"131", label:"terms · 23 resources"},
      {value:"328", label:"sources"}, {value:"15", label:"accounts · 86 project roles"}, {value:"21 512", label:"audit events"}
    ],
    records: [
      {code:"project", title:"Project and topic", text:"The context that contains records: members, status, and the parent topic."},
      {code:"H-*", title:"Claim", text:"A statement we consider true, together with an observation that would falsify it."},
      {code:"E-*", title:"Run", text:"A reproducible test protocol linked to a claim."},
      {code:"R-*", title:"Measurement", text:"A run's output: numbers, an artifact, or an observation with its scope of validity."},
      {code:"P-*", title:"Rule", text:"How the lab has decided to proceed. Status is stored explicitly; most rules are still proposed."},
      {code:"D-*", title:"Derivation", text:"Assumptions, reasoning, and an established result in place of an experimental run."},
      {code:"external research", title:"A paper, its sections, and its claims", text:"External work, its stored text, testable claims, and links to our work. An external claim does not become our measurement."},
      {code:"context", title:"Observation, term, resource", text:"Factual observations, the project's glossary, and shared lab hardware."},
      {code:"administration", title:"Source, change history, access", text:"Where a record came from, what changed, who participates, and which keys they hold."}
    ],
    writeFlow: ["Choose the project and record type", "Search for duplicates and related records", "Show the owner exactly what will be saved", "The service checks access and saves the appropriate record type", "Read the saved record back and return its code"],
    readFlow: ["Validate the key", "Identify the project in question", "Search both words and relationships", "Return records, their sources, and contradictions"],
    operations: [
      {title:"Search and graph", mode:"read", names:["search_lab","find_similar","get_related","get_timeline","recent_changes","related_by_terms","lab_health","who_works_on_what"]},
      {title:"Projects and topics", mode:"read and write", names:["list_projects","get_project_by_slug","get_project_context","list_themes","get_theme_context","create_project","set_project_status","set_project_theme","set_project_links","set_project_open_questions","assign_public_code"]},
      {title:"Scientific record chain", mode:"read and write", names:["get_hypothesis","list_hypotheses","list_derivations","create_hypothesis","update_hypothesis","record_experiment","update_experiment_status","record_evidence","record_derivation","update_derivation_status","propose_decision","update_decision"]},
      {title:"Library", mode:"read and write", names:["get_paper","list_recent_papers","list_paper_claims","find_related_papers","upsert_paper","add_paper_section","record_paper_claim","link_paper","set_record_papers"]},
      {title:"Lab context", mode:"read and write", names:["list_terms","list_lab_resources","list_journal","define_term","upsert_resource","record_journal","publish_source_note","upsert_projection_ref"]},
      {title:"Yonote", mode:"read and write", names:["preview_yonote_task","list_yonote_tasks","provision_project_workspace","upsert_yonote_task","upsert_call_note"]},
      {title:"Access and lifecycle", mode:"read and write", names:["list_agent_tokens","invite_member","issue_agent_token","revoke_agent_token","delete_project","delete_record"]}
    ],
    liveExample: {project:"Example of linked records", status:"illustration", empirical:"Claim → run → measurement → rule: each record has its own code, status, and provenance", theory:"Paper claims and derivations connect to the same chain through typed relationships; they do not replace measurements", note:"This example illustrates the response format. Private record contents and project names are not copied into the showcase."},
    boundaries: ["Obsidian stores private drafts", "Yonote stores tasks and a concise project overview for people", "MemPalace stores agent history", "Lab Knowledge stores shared scientific history, the library, working context, access permissions, and change history"],
    links: [{label:"The public knowledge model", url:"https://github.com/Vepricov/claude-brainlab/blob/main/docs/knowledge-base.md"}, {label:"BRAIn Lab toolkit", url:"https://github.com/Vepricov/claude-brainlab"}],
    runtime:["lab-knowledge-user.service · the MCP service on port 8001","lab-site.service · a separate read-only showcase","lab-knowledge-legacy-db-bridge.service · a temporary bridge to the old database","brainlab-reverse-tunnel.service · a private connection to port 8001"],
    sourceStatus:"The running service exposes 58 tools and matches the deployed source code. The calling agent is responsible for showing a proposed write to the owner and reading it back; there are no separate tools for these steps. All counts were collected on 09-09-2026 by querying the database directly, including papers, sources, accounts, and the change log. Previously, those counts came from a snapshot one day older because no listing tools were available for them."
  },
  journeys: [
    {
      "id": "paper",
      "label": "Write a paper",
      "title": "From an idea to a paper",
      "intro": "Start with a research question. Develop it into a testable result, a manuscript, and a response to reviewers.",
      "color": "#c8ed93",
      "note": "A review may send you back to the experiments or the manuscript. You can revisit any stage.",
      "edges": [
        [
          0,
          1
        ],
        [
          1,
          2
        ],
        [
          2,
          3
        ],
        [
          3,
          4
        ],
        [
          4,
          5
        ],
        [
          5,
          6
        ],
        [
          6,
          7
        ]
      ],
      "stages": [
        {
          "id": "project",
          "title": "Question",
          "caption": "Project context",
          "point": [
            12,
            18
          ],
          "action": "Define what you want to find out and set up the research workspace.",
          "inputs": "An idea, an existing repository, and notes. For ongoing work, first recover the current decisions.",
          "check": "The project hub states the question, the scope, and the next test.",
          "tools": [
            {
              "process": "projects",
              "tool": "create-project"
            },
            {
              "process": "projects",
              "tool": "restore-session"
            },
            {
              "process": "projects",
              "tool": "obsidian-project-memory"
            }
          ]
        },
        {
          "id": "literature",
          "title": "Literature",
          "caption": "Related work",
          "point": [
            37,
            12
          ],
          "action": "Find the closest methods and examine what their results establish.",
          "inputs": "The research question, key papers, and search scope. Hermes helps discover papers; selected works enter the library.",
          "check": "Each comparison method has a primary source. The difference from your idea is stated explicitly.",
          "tools": [
            {
              "process": "literature",
              "tool": "paperscout"
            },
            {
              "process": "literature",
              "tool": "paper-search"
            },
            {
              "process": "literature",
              "tool": "paper-ingest"
            }
          ]
        },
        {
          "id": "hypothesis",
          "title": "Hypothesis",
          "caption": "Test criterion",
          "point": [
            63,
            18
          ],
          "action": "Turn the idea into a claim that an experiment could falsify.",
          "inputs": "Findings from the literature, a proposed mechanism, and the available budget.",
          "check": "The baseline, metric, matched comparison conditions, and falsification criterion are recorded.",
          "tools": [
            {
              "process": "ideation",
              "tool": "research-ideation"
            },
            {
              "process": "projects",
              "tool": "grill-with-docs"
            }
          ]
        },
        {
          "id": "experiment",
          "title": "Experiment",
          "caption": "Runs and logs",
          "point": [
            86,
            31
          ],
          "action": "Ask Hermes to implement and run the agreed test.",
          "inputs": "The protocol, code, authorized resources, and stopping conditions. Long-running work can be handed to a project watcher.",
          "check": "Each run retains its configuration and actual status. An unfinished run is not presented as a completed result.",
          "tools": [
            {
              "process": "experiments",
              "tool": "hermes"
            },
            {
              "process": "experiments",
              "tool": "experiment-log"
            },
            {
              "process": "experiments",
              "tool": "handoff-to-jarvis"
            }
          ]
        },
        {
          "id": "results",
          "title": "Results",
          "caption": "Tables and figures",
          "point": [
            82,
            71
          ],
          "action": "Compare runs and prepare figures for the paper.",
          "inputs": "Logs, configurations, and information about repeated runs. Check comparability before plotting.",
          "check": "Every point links to its source data. The number of repeats and the limits of the conclusion are stated.",
          "tools": [
            {
              "process": "results",
              "tool": "results-analysis"
            },
            {
              "process": "results",
              "tool": "academic-plotting"
            },
            {
              "process": "results",
              "tool": "results-report"
            }
          ]
        },
        {
          "id": "manuscript",
          "title": "Manuscript",
          "caption": "A coherent argument",
          "point": [
            57,
            80
          ],
          "action": "Build the manuscript around the verified result and check the argument's progression.",
          "inputs": "The problem formulation, method, tables, figures, and verified sources.",
          "check": "Each section answers a specific question, and transitions guide the reader from the problem to the conclusions.",
          "tools": [
            {
              "process": "writing",
              "tool": "ml-paper-writing"
            },
            {
              "process": "writing",
              "tool": "reverse-outline-flow-check"
            }
          ]
        },
        {
          "id": "review",
          "title": "Review",
          "caption": "Manuscript feedback",
          "point": [
            32,
            71
          ],
          "action": "Critically review the manuscript and verify its citations separately.",
          "inputs": "The full manuscript, appendix, bibliography, and venue requirements.",
          "check": "Strong claims have supporting data, references are verified, and substantive issues are addressed.",
          "tools": [
            {
              "process": "writing",
              "tool": "astar-paper-review"
            },
            {
              "process": "writing",
              "tool": "citation-verification"
            }
          ]
        },
        {
          "id": "response",
          "title": "Peer reviews",
          "caption": "Response and revision",
          "point": [
            10,
            80
          ],
          "action": "Analyze the reviews and prepare a response backed by verifiable changes.",
          "inputs": "The reviews, the submitted version, and any available additional results.",
          "check": "Every point receives a substantive answer. Promised changes have actually been made.",
          "tools": [
            {
              "process": "writing",
              "tool": "review-response"
            },
            {
              "process": "writing",
              "tool": "reverse-outline-flow-check"
            }
          ]
        }
      ]
    },
    {
      "id": "discovery",
      "label": "Build on another idea",
      "title": "From reading to your own research",
      "intro": "Found an interesting paper? Determine what follows from it and which hypothesis of your own is worth testing.",
      "color": "#a9cbe8",
      "note": "If the first test does not support the idea, revisit the hypothesis and comparison conditions.",
      "edges": [
        [
          0,
          1
        ],
        [
          1,
          2
        ],
        [
          2,
          3
        ],
        [
          3,
          4
        ]
      ],
      "stages": [
        {
          "id": "read",
          "title": "Understand",
          "caption": "Paper and reading note",
          "point": [
            13,
            24
          ],
          "action": "Read the source and save it alongside your own analysis.",
          "inputs": "A DOI, arXiv link, or PDF, plus the question that motivates your reading.",
          "check": "The main result, assumptions, and limitations are separated from your interpretation.",
          "tools": [
            {
              "process": "literature",
              "tool": "paper-ingest"
            },
            {
              "process": "literature",
              "tool": "want-2-read"
            },
            {
              "process": "literature",
              "tool": "obsidian-literature-workflow"
            }
          ]
        },
        {
          "id": "compare",
          "title": "Compare",
          "caption": "Position among existing methods",
          "point": [
            45,
            13
          ],
          "action": "Find related work and check whether the result applies to your problem.",
          "inputs": "The paper and your task's conditions: data, model, and compute budget.",
          "check": "You have a comparison of approaches and a specific unresolved gap.",
          "tools": [
            {
              "process": "literature",
              "tool": "paperscout"
            },
            {
              "process": "literature",
              "tool": "paper-search"
            },
            {
              "process": "projects",
              "tool": "grill-with-docs"
            }
          ]
        },
        {
          "id": "discuss",
          "title": "Discuss",
          "caption": "Objections and decisions",
          "point": [
            81,
            29
          ],
          "action": "Discuss the idea with colleagues and preserve the decisions from the conversation.",
          "inputs": "A meeting recording for Brain Call, or an existing transcript for call-notes. Skip this stage if there was no discussion.",
          "check": "The owner has confirmed the decisions and tasks. Only the agreed material may enter the shared database.",
          "tools": [
            {
              "process": "calls",
              "tool": "brain-call"
            },
            {
              "process": "calls",
              "tool": "call-notes"
            }
          ]
        },
        {
          "id": "design",
          "title": "Formulate",
          "caption": "Your hypothesis",
          "point": [
            67,
            71
          ],
          "action": "Choose one change and design the smallest meaningful test.",
          "inputs": "The gap identified in the review and objections raised during discussion.",
          "check": "It is clear which result would support the hypothesis, which would falsify it, and what is being compared.",
          "tools": [
            {
              "process": "ideation",
              "tool": "research-ideation"
            },
            {
              "process": "projects",
              "tool": "create-project"
            }
          ]
        },
        {
          "id": "pilot",
          "title": "Test",
          "caption": "Pilot result",
          "point": [
            24,
            77
          ],
          "action": "Run a pilot and decide whether further research is justified.",
          "inputs": "A minimal protocol, authorized resources, and a stopping criterion.",
          "check": "The pilot is analyzed together with its settings. A single run is not presented as a robust effect.",
          "tools": [
            {
              "process": "experiments",
              "tool": "hermes"
            },
            {
              "process": "experiments",
              "tool": "experiment-log"
            },
            {
              "process": "results",
              "tool": "results-analysis"
            }
          ]
        }
      ]
    },
    {
      "id": "share",
      "label": "Prepare a talk and a post",
      "title": "From a result to an audience",
      "intro": "Start with a paper or verified results. Build an explanation, then choose a talk, a post, or both.",
      "color": "#e4b5b7",
      "note": "A talk and a post are independent branches. You do not need slides before writing a post.",
      "edges": [
        [
          0,
          1
        ],
        [
          1,
          2
        ],
        [
          1,
          3
        ]
      ],
      "stages": [
        {
          "id": "story",
          "title": "Message",
          "caption": "What the audience needs",
          "point": [
            14,
            44
          ],
          "action": "Choose what the listener or reader should understand about the work.",
          "inputs": "The paper or report, the audience, and the format of the talk or post.",
          "check": "The main finding can be explained without exaggeration. You know which details this audience needs.",
          "tools": [
            {
              "process": "results",
              "tool": "results-report"
            },
            {
              "process": "writing",
              "tool": "reverse-outline-flow-check"
            }
          ]
        },
        {
          "id": "figures",
          "title": "Illustrations",
          "caption": "Visible evidence",
          "point": [
            43,
            44
          ],
          "action": "Prepare figures that make the result clear.",
          "inputs": "Source data, existing tables, and the conclusion each figure should support.",
          "check": "Labels are readable at the intended size. Scales and comparisons preserve the meaning of the source data.",
          "tools": [
            {
              "process": "results",
              "tool": "academic-plotting"
            }
          ]
        },
        {
          "id": "talk",
          "title": "Talk",
          "caption": "Slides and rehearsal",
          "point": [
            80,
            20
          ],
          "action": "Build a research talk and rehearse it.",
          "inputs": "The paper, figures, audience, and available time. The presentation skill prepares the outline, LaTeX/Beamer source, and PDF.",
          "check": "The PDF has been compiled and inspected. Timing is verified by rehearsal, not inferred from the slide count.",
          "tools": [
            {
              "process": "presentation",
              "tool": "presentation-skill"
            }
          ]
        },
        {
          "id": "post",
          "title": "Post",
          "caption": "Publication draft",
          "point": [
            80,
            73
          ],
          "action": "Adapt the work for Telegram, X, or Habr.",
          "inputs": "The research text, verified illustrations, platform, and disclosure restrictions.",
          "check": "Facts have been checked against the research and sources are cited. The author has reviewed the text before publication.",
          "tools": [
            {
              "process": "presentation",
              "tool": "paper-to-social"
            }
          ]
        }
      ]
    }
  ]
};
