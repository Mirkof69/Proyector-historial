# Pull Request

## Description

<!-- Provide a concise description of what this PR does and why it is needed -->

**Type of change:**

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Database migration
- [ ] Configuration change
- [ ] Documentation update
- [ ] Refactoring (no functional change)
- [ ] Dependency update
- [ ] CI/CD change

## Related Issues

<!-- Link related issues using #issue_number. Example: Closes #42 -->

- Closes #
- Related to #

## Changes Made

<!-- List the key changes in this PR -->

-
-
-

## Database Changes

<!-- If this PR includes database migrations, describe them here -->

- [ ] No database changes
- [ ] Django migrations included (`python manage.py makemigrations`)
- [ ] Migrations are reversible
- [ ] Data migration included (if applicable)

**Migration files:**

-

## Testing

<!-- Describe the tests you ran and how to reproduce them -->

### Backend (Django)

- [ ] All existing tests pass (`python manage.py test`)
- [ ] New tests added for new functionality
- [ ] Manual testing completed
- [ ] API endpoints tested (if applicable)

### Frontend (React)

- [ ] All existing tests pass (`npm test`)
- [ ] TypeScript compiles without errors (`tsc --noEmit`)
- [ ] ESLint passes (`npm run lint`)
- [ ] Build succeeds (`npm run build`)
- [ ] UI tested in browser

### Docker

- [ ] Docker images build successfully
- [ ] Docker Compose services start without errors
- [ ] Services communicate correctly (backend, frontend, AI service, database)

## Screenshots / Recordings

<!-- If this PR changes the UI, include screenshots or screen recordings -->

<details>
<summary>Before</summary>

<!-- Add screenshots -->

</details>

<details>
<summary>After</summary>

<!-- Add screenshots -->

</details>

## Environment Variables

<!-- List any new or changed environment variables -->

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
|          |             |          |         |

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Security Considerations

<!-- Note any security implications of this PR -->

- [ ] No sensitive data exposed in logs or responses
- [ ] Input validation added/updated (if applicable)
- [ ] Authentication/authorization reviewed (if applicable)
- [ ] SQL injection risks considered (if applicable)
- [ ] XSS risks considered (if applicable)

## Deployment Notes

<!-- Any special instructions for deploying this PR -->

- [ ] No special deployment steps required
- [ ] Requires database migration on deploy
- [ ] Requires environment variable changes
- [ ] Requires service restart
- [ ] Requires cache clear

**Deployment steps:**

1.
2.
3.

## Additional Notes

<!-- Any additional context, decisions made, or things reviewers should know -->
