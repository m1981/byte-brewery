DEFAULT_CONFIG_YAML = """
definitions:
  - id: push_diff
    tag: git_changes
    cmd: "internal:push_diff"
  - id: file_tree
    tag: project_structure
    cmd: "ls -R"

prompts:
  - id: basic_reviewer
    text: "You are a code reviewer. Return JSON: {\\"status\\": \\"PASS\\" | \\"FAIL\\", \\"reason\\": \\"...\\"}"

checks:
  - id: sanity_check
    prompt_id: basic_reviewer
    model: gpt-3.5-turbo
    context: [push_diff]
    max_chars: 16000
"""