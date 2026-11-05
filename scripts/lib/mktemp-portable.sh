#!/usr/bin/env bash
# Portable mktemp helpers for GNU coreutils (linux CI) and BSD mktemp (macOS).
# shellcheck shell=bash

mat_mktemp_file() {
  local prefix="${1:?prefix required}"
  mktemp "${TMPDIR:-/tmp}/${prefix}.XXXXXX"
}
