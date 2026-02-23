# Claude Pull Request Review Guidance

This repository is a local-first manufacturing analytics system.

Claude should prioritize:

1. Preservation of deterministic pricing calculations.
2. Strict architectural separation:
   - routers contain no business logic
   - services contain calculations
   - parsers act only as translators
3. Compliance with PROJECT.md milestone ordering.
4. Backwards compatibility of API endpoints.
5. Successful execution of tools/verify_project.py.

Reject suggestions introducing:
- SaaS patterns
- authentication systems
- cloud dependencies
- background workers
- unnecessary infrastructure.
