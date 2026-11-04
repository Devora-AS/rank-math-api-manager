# Task: Assess external automation suitability

## Goal
Decide whether Rank Math's internal REST endpoints are appropriate for external automation such as n8n, or whether a wrapper plugin endpoint is safer.

## What to return
- confirmed auth pattern from source
- permission callback summary
- risks of coupling directly to Rank Math's internal payload shape
- recommendation: direct use vs wrapper plugin
- minimal safe wrapper design if recommended

## Acceptance criteria
- distinguishes confirmed nonce/cookie auth from runtime-verify auth options
- mentions capability checks
- mentions field allowlisting and sanitization for wrapper design
