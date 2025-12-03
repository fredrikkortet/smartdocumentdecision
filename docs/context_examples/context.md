# context.md - User Preferences for Smart Read Agent

# general
display_name: "Alice - Engineering Manager"
decision_mode: "hybrid"   # options: strict | hybrid | lenient

# thresholds (0-100)
relevancy_threshold: 70    # >= => recommend full read
confidence_threshold: 0.75

# document preferences
preferred_doc_types:
  - "technical report"
  - "research paper"
ignored_doc_types:
  - "marketing"
  - "ads"

# focus areas (keywords or phrases)
focus_areas:
  - "architecture"
  - "performance"
  - "security"
  - "cost analysis"

# length handling
max_pages_full_read: 20    # if > this, prefer key info unless high relevancy

# reading style
summary_length: "short"    # short|medium|long
show_chunk_summaries: true

# rules (optional declarative logic)
rules:
  - name: "Ignore marketing fluff"
    if_contains: ["campaign", "press release", "ad"]
    action: "prefer_key_info"

# example notes for the user
notes:
  - "Change relevancy_threshold to be stricter if you only want critical docs recommended for full read."
