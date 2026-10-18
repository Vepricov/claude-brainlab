window.SYSTEM_EXAMPLES = {
  verified: "09-09-2026",
  surfaces: {
    obsidian: {
      number: "P1",
      title: "Obsidian",
      kicker: "Personal research memory",
      promise: "A place for detailed understanding, drafts, a research log, and private project context.",
      owns: ["The whole lab tree ~/brainlab: the same folders as in GitLab", "Personal material next to the work: notes/, daily/, runs/ do not go to GitLab", "Operon boards with personal tasks"],
      doesNotOwn: ["A separate copy of knowledge: Obsidian reads the same files as git", "Team tasks: they are in GitLab", "An agent's automatic session history"],
      path: ["Working material appears in the work", "Personal material stays in its notes/ and daily/", "Knowledge is written up in claims/ of the same work", "A person merges the merge request, and it shows up in the same tree after git pull"],
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
    tasks: {
      number: "P3",
      title: "GitLab issues",
      kicker: "Team assignments",
      promise: "Issues and the board live in the same work repository that knowledge is written to. There is no second board next to it.",
      owns: ["Work issues: assignee, deadline, the claim the issue affects", "Work board: columns by labels", "Linking an issue to a merge request: “Closes #N” closes it on merge"],
      doesNotOwn: ["Knowledge itself: claims, runs, and series live in claims/", "Raw logs and personal notes", "A second copy of the claims"],
      path: ["An agreement becomes an issue in the work repository", "The assignee sees it at session start", "The work goes out as a merge request that links the issue", "The merge closes the issue by itself"],
      routes: [
        {kind:"Workflow", title:"Projects and memory", text:"How a work is created, who leads it, and where its issues are.", process:"projects", tool:"obsidian-project-bootstrap"}
      ],
      links: [{label:"How to set it up", url:"https://github.com/brain-lab-research/claude-brainlab/blob/main/docs/onboarding.md"}]
    }
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
