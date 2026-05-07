---
name: release
description: 'Trigger the publish workflow and downstream actions'
argument-hint: 'Optional GitHub username for cloning Ops'
user-invocable: true
---

# Release skill

This skill releases the `api_demo_server` package and prepares updates to the Ops docs.

## When to use
- You want to run `/release` in Copilot Chat.

## Procedure

This procedure is structured with a subheading for each high-level step. If a high-level step fails, stop the procedure immediately and tell the user.

### Check that we're on `canonical:master` and up-to-date

1. Run `git branch --show-current` and check that the current branch is `master`.
2. Run `git remote get-url origin` and check that `origin` is from the `canonical` org.
3. Run `git pull --ff-only --tags origin master`.

### Check version numbers

1. Grab the pre-release version number from `api_demo_server/__init__.py`.
2. Check that the version number matches the example in `README.md`.
3. Make a note of the pre-release version number - you'll need it in the next steps.

### Check existing tags

1. Check that a tag doesn't already exist for the pre-release version number.

### Push a new tag

1. Run `git tag <version> origin/master` where `<version>` is the pre-release version number.
2. Run `git push origin <version>`.

### Clone Ops

If the user provided an argument after `/release`:

1. Treat the argument as the user's GitHub username.
2. At the root of our repo, run `uvx gimmegit --allow-nested -u canonical <username>/operator update-demo-image`.

Alternatively, if the user didn't provide an argument:

1. At the root of our repo, run `uvx gimmegit --allow-nested canonical/operator update-demo-image`. This command clones Ops in a subdirectory and checks out a new branch.
2. Make a note of the Ops clone directory (from the gimmegit output) - you'll need it in the next steps.

### Update the Ops docs

1. In the Ops clone directory, search `docs/*` for references to `api_demo_server`.
2. If a version number is mentioned, replace the version number by the pre-release version number.
3. Commit the changes with a message like 'bump api_demo_server in docs'.

### Update the Ops example charms

1. In the Ops clone directory, search `examples/*` for references to `api_demo_server`.
2. If a version number is mentioned, replace the version number by the pre-release version number.
3. Commit the changes with a message like 'bump api_demo_server in example charms'.

### Push the Ops changes

1. In the Ops clone directory, run `git push`.
2. Run `gimmegit --compare` so that the user can inspect all the changes in GitHub before opening a PR.

### Wrap-up

1. Remind the user that pushing a tag has triggered the publish workflow. They should check the progress at https://github.com/canonical/api_demo_server/actions.
2. Remind the user to inspect the new Ops branch in GitHub and open a PR after the publish workflow has completed.
