# Task: Design a wrapper endpoint

## Goal
Design a custom WordPress plugin REST endpoint that safely exposes only the Rank Math fields needed by an external automation workflow.

## What to return
- proposed route namespace and path
- permission model
- request schema
- sanitization rules per field
- storage/update strategy
- example success and error responses

## Acceptance criteria
- avoids exposing arbitrary `meta` passthrough
- uses explicit field allowlisting
- uses WordPress capability checks tied to the target object
- documents auth expectations for external callers
