# Planning Decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Every high finding is staged | The analysis reported no critical issues and 10 high issue rows; split memory safety into gzip and SMUGGLE stages for closability. | Merging all high work into one security stage. |
| Constraints-first CI assumption for early stages | Current CI/Docker already use `constraints/ci.txt`; adopting uv is a later explicit decision. | Switching immediately to uv across CI/Docker without team confirmation. |
| Docs fixes are staged separately from behavior changes | Some API mismatches can be fixed safely by documenting current behavior, while implementation normalization would be compatibility-affecting. | Combining docs drift with backend behavior stages. |
| No low-priority polish stages by default | User did not pass `--include-low`; low items remain in backlog unless they are bundled with related medium/high work. | Inflating the plan with standalone polish stages. |
| Inspector asset before redaction | Redaction work depends on deciding that `inspector.js` is an intentional first-class asset. | Editing an untracked module without making its packaging status explicit. |
