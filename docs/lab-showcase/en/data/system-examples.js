window.SYSTEM_EXAMPLES = {
  "verified": "19-10-2026",
  "surfaces": {
    "obsidian": {
      "number": "P1",
      "title": "Obsidian",
      "kicker": "The lab tree in one window",
      "promise": "Obsidian opens the ~/brainlab tree itself: personal notes and the shared base live in the same work folders, but only the shared part goes to GitLab.",
      "owns": [
        "Personal in every work: notes/, daily/, runs/ are excluded from git and stay on the machine",
        "Shared in the same folders: claims/<CODE>/ with runs, series and derivations, plus the topic's literature",
        "Personal Operon boards: the reading queue and your own tasks",
        "Personal folders sync to the do-vpn server via Syncthing, and Hermes works in the same tree"
      ],
      "doesNotOwn": [
        "A second copy of the base: writing to the shared part is a git push, not a sync",
        "Team tasks: they live in GitLab",
        "The agent's session history: it lives in MemPalace"
      ],
      "path": [
        "People and agents edit files right in the work's clone",
        "Personal stays in notes/ and daily/, git does not see it",
        "Shared goes out as a branch, and git push opens a proposal to the work lead by itself",
        "Checks verify numbers and text, a person merges: the merge is the record"
      ],
      "routes": [
        {
          "kind": "Workflow",
          "title": "Projects and memory",
          "text": "How a work is created, where its README lives and what goes from it to GitLab.",
          "process": "projects",
          "tool": "create-project"
        }
      ],
      "links": [
        {
          "label": "Obsidian",
          "url": "https://obsidian.md/"
        },
        {
          "label": "How the tree is laid out",
          "url": "https://github.com/Vepricov/claude-brainlab#the-vault-is-the-tree"
        }
      ]
    },
    "mempalace": {
      "number": "P2",
      "title": "MemPalace",
      "kicker": "The agent's personal long-term memory",
      "promise": "Gives the agent back past decisions, the owner's words and working history, so a new session starts where the last one ended.",
      "owns": [
        "A session diary in the compressed AAAK format",
        "Drawers of verbatim content: the owner's words, decisions with reasons, measured numbers",
        "A knowledge graph: links between people, works and decisions"
      ],
      "doesNotOwn": [
        "The lab's shared knowledge: it lives in git, in the works' claims/",
        "Server and run state without a live check",
        "A person's personal notes: they live in the work's notes/"
      ],
      "path": [
        "When the past comes up, the agent searches MemPalace first, then the ~/brainlab tree",
        "Gets episodes together with where they came from",
        "Re-checks volatile facts against the live system",
        "At the end of a turn Jev suggests what to save from it and where: MemPalace or the base"
      ],
      "routes": [
        {
          "kind": "Workflow",
          "title": "Memory and shared knowledge",
          "text": "Where the agent's personal memory ends and the shared base in git begins.",
          "process": "memory",
          "tool": "mempalace"
        }
      ],
      "links": [
        {
          "label": "MemPalace on GitHub",
          "url": "https://github.com/MemPalace/mempalace"
        }
      ]
    },
    "yonote": {
      "number": "P3",
      "title": "GitLab: issues and boards",
      "kicker": "Team tasks next to the knowledge",
      "promise": "A work's task is an issue in that work's own GitLab repository, and the board is a view of those issues by label. The task and the claim it moves forward live in one place.",
      "owns": [
        "Work tasks: assignee, due date, label and the claim the task affects",
        "The work's board: columns by the labels “in progress” and “in review”",
        "Proposals with the checks' verdict",
        "Operations: grants, management, education, in a separate private ops group"
      ],
      "facts": [
        "02-10-2026: 124 tasks from 25 boards moved over from Yonote",
        "30 call records landed in calls/<date>.md of their works",
        "An issue's body names the claim it affects (rule task-names-its-claim)",
        "GitLab sends no emails: assignments are announced by To-Dos on the site and by a Telegram bot",
        "Hermes has his own hermes kanban board: 381 closed tasks on rl-muon"
      ],
      "doesNotOwn": [
        "Personal tasks and the reading queue: they live on Operon boards in Obsidian",
        "Raw call recordings: calls/raw/ is excluded from git",
        "The merge decision: the work lead makes it, not the agent"
      ],
      "path": [
        "An issue is created in the work's repository and names its claim",
        "lab tasks shows the open ones, lab take sets the assignee and the “in progress” label",
        "Work goes out as a branch and a proposal, and a Closes #N line closes the issue on merge",
        "lab checks shows the checks' verdict, the lead merges"
      ],
      "routes": [
        {
          "kind": "Workflow",
          "title": "A new work",
          "text": "A repository in its topic, a README with the lead and team, a protected main and a board.",
          "process": "projects",
          "tool": "create-project"
        },
        {
          "kind": "Calls",
          "title": "From a call to tasks",
          "text": "The call's outcome goes into the work's calls/<date>.md, the tasks into its issues.",
          "process": "calls",
          "tool": "call-notes"
        }
      ],
      "links": [
        {
          "label": "For lab members",
          "url": "https://github.com/Vepricov/claude-brainlab#for-brain-lab-members"
        }
      ]
    }
  },
  "liveMcp": {
    "title": "The knowledge base in GitLab, live",
    "subtitle": "What the lab has already tested lives in git: one work, one repository, and a claim is a claims/<CODE>/ folder. Below: how to find a record, how it is read and how it is written to.",
    "verifiedAt": "19-10-2026",
    "deployment": {
      "host": "The lab's GitLab CE on the brain_lab server",
      "service": "git: repositories of works, topic literature, handbook, journal, servers",
      "endpoint": "everyone has it locally: the ~/brainlab tree at the same paths as in GitLab",
      "revision": "a version is a commit in main, the history of any page is git log",
      "state": "the MCP service and the PostgreSQL database were removed on 07-10-2026, there is no other knowledge store"
    },
    "counts": [
      {
        "value": "29",
        "label": "works with claims"
      },
      {
        "value": "135",
        "label": "claims"
      },
      {
        "value": "1 010",
        "label": "run pages"
      },
      {
        "value": "376",
        "label": "series"
      },
      {
        "value": "225",
        "label": "derivations"
      },
      {
        "value": "735",
        "label": "paper reviews across 25 topics"
      },
      {
        "value": "55",
        "label": "named rules in the canon.md canon"
      }
    ],
    "records": [
      {
        "code": "H-DYC-007",
        "title": "DyKAF instead of SOAP lowers validation loss in language model pretraining",
        "text": "dykaf · under test. The claim folder holds 114 runs, 21 series and 6 derivations: everything used to test it sits right next to it."
      },
      {
        "code": "H-DYC-005",
        "title": "DyKAF's overhead on SOAP's step time shrinks as data passes take up a larger share of the step",
        "text": "dykaf · inconclusive. 12 runs, 6 series. “Not established” is a legitimate verdict, and it is recorded, not hidden."
      },
      {
        "code": "H-KAW-002",
        "title": "For BanLast the paper's 3x speedup does not reproduce: a direct count gives 1.7x",
        "text": "kawasaki · refuted. A negative result is a record too: nobody will run this test a second time."
      },
      {
        "code": "H-SXL-009",
        "title": "SimplexLoRA gives the best GLUE average among hyperparameter-free methods on DeBERTaV3-base",
        "text": "simplex-lora · supported. 4 runs, 2 series."
      },
      {
        "code": "H-SFS-006",
        "title": "SoftMuon lowers perplexity relative to Muon at three pretraining scales and has a better mean rank on graph tasks",
        "text": "softsign · supported. 7 runs, 3 series, 1 derivation."
      }
    ],
    "writeFlow": [
      "A claim/<CODE> branch in the work's clone from the tree",
      "The run page is written by the lab_run.py recorder, the agent adds only “what is seen”",
      "git push opens a proposal and assigns the work lead by itself",
      "The checks match every number against the runs, a judge reads the text",
      "The lead merges: the merge is the record"
    ],
    "readFlow": [
      "lab sync assembles and updates the ~/brainlab tree",
      "git pull in the clone: what is new in the work",
      "rg over the tree, or Obsidian and GitLab search, over the same files",
      "git log and git blame: who wrote a line, when and why"
    ],
    "operations": [
      {
        "title": "Tree",
        "mode": "read",
        "names": [
          "lab sync",
          "lab here <work>",
          "git pull"
        ]
      },
      {
        "title": "Search",
        "mode": "read",
        "names": [
          "rg -i 'muon' ~/brainlab",
          "git grep -n 'H-WSD-009'",
          "git log -S 'E-WSD-031'",
          "git blame"
        ]
      },
      {
        "title": "Tasks",
        "mode": "read and write",
        "names": [
          "lab tasks",
          "lab take <number>",
          "Closes #N"
        ]
      },
      {
        "title": "Writing to a work",
        "mode": "via a proposal",
        "names": [
          "git switch -c claim/<CODE>",
          "lab_run.py",
          "git push",
          "lab checks"
        ]
      },
      {
        "title": "Literature and service repos",
        "mode": "straight to main",
        "names": [
          "paper-ingest",
          "git pull --rebase",
          "git push"
        ]
      }
    ],
    "liveExample": {
      "project": "H-DYC-007 · dykaf",
      "status": "under test",
      "empirical": "Claim → 114 runs → 21 series: every run is recorded by code, every number has an address where you can see it",
      "theory": "6 derivations in theory/ next to the runs, each with a mandatory “Proof” section",
      "note": "dykaf is the only work open to everyone logged into GitLab, so the example comes from it. Texts of private works are not copied to the showcase."
    },
    "boundaries": [
      "Obsidian is a window into the ~/brainlab tree: personal content in notes/, daily/, runs/ stays on the machine",
      "GitLab holds shared knowledge and tasks: works, topic literature, issues and boards",
      "MemPalace is the agent's personal memory across sessions",
      "Hermes handles execution and long conversational memory on the do-vpn server"
    ],
    "links": [
      {
        "label": "How the base is built",
        "url": "https://github.com/Vepricov/claude-brainlab#lab-knowledge-the-shared-research-base"
      },
      {
        "label": "BRAIn Lab toolkit",
        "url": "https://github.com/Vepricov/claude-brainlab"
      }
    ],
    "runtime": [
      "GitLab CE 17.11 in rootless podman on brain_lab",
      "checks are triggered by a GitLab event, not a schedule: a proposal opened or updated gets a verdict",
      "the “base” gate (numbers, codes, links, deletions) and the “lab/prose” gate (text judge) block the merge",
      "for the owner, lab sync runs by itself every three hours, and on do-vpn a cron job updates the same tree"
    ],
    "sourceStatus": "Numbers counted on 19-10-2026 over the owner's ~/brainlab tree: claims/H-* folders in works, E-*, S-*, D-* pages under them, topic literature pages excluding README, canon rules by heading. The MCP service this page used to show was removed on 07-10-2026 together with the PostgreSQL database, and its counters are not carried over."
  },
  "journeys": [
    {
      "id": "paper",
      "label": "Write a paper",
      "title": "From an idea to a paper",
      "intro": "The path by which a question becomes a paper. Every step leaves a trace in the base, and a reviewer can walk it backwards: from a conclusion to the run its number came from.",
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
          "action": "State what you want to find out and create a work: a repository in your topic and a README with the lead and team.",
          "inputs": "An idea, an existing repository and notes. For work already under way, first pull up past decisions from MemPalace and the work's README.",
          "check": "The work's README records the question, the lead and the next test, and the clone sits in its place in the tree.",
          "tools": [
            {
              "process": "projects",
              "tool": "create-project"
            },
            {
              "process": "memory",
              "tool": "mempalace"
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
          "inputs": "The research question and key papers. Every morning Jev selects fresh papers against the descriptions of our works, and paper-ingest reviews the chosen ones.",
          "check": "The compared methods have reviews in the topic's literature with a citation key. The difference from your idea is stated explicitly.",
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
          "check": "claims/<CODE>/ records the baseline method, the metric, identical comparison conditions and the refutation criterion.",
          "tools": [
            {
              "process": "ideation",
              "tool": "research-ideation"
            },
            {
              "process": "ideation",
              "tool": "grill-with-docs"
            },
            {
              "process": "memory",
              "tool": "lab-knowledge-skill"
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
          "action": "Wrap training in the lab_run.py recorder and hand launching and monitoring to Hermes.",
          "inputs": "Protocol, code, allowed servers and a stop condition. Hermes wakes up by himself when a run finishes, and a long series can be handed to Jarvis.",
          "check": "Every run page was written by code: hyperparameters, metrics, commit, hardware. An unfinished run is not passed off as a result.",
          "tools": [
            {
              "process": "experiments",
              "tool": "hermes"
            },
            {
              "process": "results",
              "tool": "lab-run"
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
          "action": "Gather the runs into a series with a verdict and build the figures for the paper.",
          "inputs": "Run pages, configs and seeds. Check comparability first, then plot.",
          "check": "Every number in the text is in the runs, otherwise the checks give a red verdict. The number of repeats and the limits of the conclusion are stated.",
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
              "tool": "proposal-gates"
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
              "tool": "writing-anti-ai"
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
          "check": "Strong claims are backed by data. The hook refuses to write a \\cite with a key missing from references.bib.",
          "tools": [
            {
              "process": "writing",
              "tool": "astar-paper-review"
            },
            {
              "process": "writing",
              "tool": "citation-verification"
            },
            {
              "process": "writing",
              "tool": "project-bibliography-gate"
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
              "tool": "ml-paper-writing"
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
          "action": "Read the source and file the review in the topic's literature.",
          "inputs": "A DOI, arXiv link, or PDF, plus the question that motivates your reading.",
          "check": "The main result, assumptions and limitations are kept apart from your interpretation. The review sits in the topic's literature and is visible to the whole lab.",
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
              "tool": "literature-library"
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
              "process": "ideation",
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
          "check": "The owner confirmed the decisions. The outcome went into the work's calls/<date>.md, the tasks into its issues, and the raw recording stayed in calls/raw/.",
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
              "process": "results",
              "tool": "lab-run"
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
              "tool": "ml-paper-writing"
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
