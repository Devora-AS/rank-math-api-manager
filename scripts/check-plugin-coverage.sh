#!/usr/bin/env bash
# Enforce minimum line coverage on rank-math-api-manager.php (default 80%).
# Requires pcov or xdebug. Usage: ./scripts/check-plugin-coverage.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MIN_LINE="${MIN_LINE_COVERAGE:-80}"
CLOVER="${CLOVER_PATH:-build/coverage/clover.xml}"
WP_TESTS_DIR="${WP_TESTS_DIR:-/tmp/wordpress-tests-lib}"

die() {
	echo "check-plugin-coverage: $*" >&2
	exit 1
}

if ! php -m 2>/dev/null | grep -qiE '^(pcov|xdebug)$'; then
	die "pcov or xdebug PHP extension required for coverage (install via setup-php in CI)."
fi

if [ ! -d "$WP_TESTS_DIR" ]; then
	die "WP_TESTS_DIR not ready ($WP_TESTS_DIR). Run ./scripts/run-phpunit-local.sh once to install the test suite."
fi

mkdir -p build/coverage

export WP_TESTS_DIR
export MIN_LINE_COVERAGE="$MIN_LINE"
export CLOVER_PATH="$CLOVER"
vendor/bin/phpunit --configuration phpunit.xml.dist --coverage-clover "$CLOVER" "$@"

php <<'PHP'
<?php
$min = (float) getenv('MIN_LINE_COVERAGE');
if ($min <= 0) {
    $min = 80.0;
}
$clover = getenv('CLOVER_PATH') ?: 'build/coverage/clover.xml';
if (! is_readable($clover)) {
    fwrite(STDERR, "check-plugin-coverage: clover file missing: {$clover}\n");
    exit(1);
}
$xml = simplexml_load_file($clover);
if (false === $xml) {
    fwrite(STDERR, "check-plugin-coverage: invalid clover XML\n");
    exit(1);
}
$target = 'rank-math-api-manager.php';
$metrics = null;
foreach ($xml->project->file as $file) {
    $name = (string) $file['name'];
    if (substr($name, -strlen($target)) === $target) {
        $metrics = $file->metrics;
        break;
    }
}
if (null === $metrics) {
    fwrite(STDERR, "check-plugin-coverage: {$target} not found in clover report\n");
    exit(1);
}
$statements = (int) $metrics['statements'];
$covered    = (int) $metrics['coveredstatements'];
if ($statements <= 0) {
    fwrite(STDERR, "check-plugin-coverage: zero statements measured\n");
    exit(1);
}
$pct = ( $covered / $statements ) * 100;
printf(
    "Coverage for %s: %.2f%% (%d/%d statements)\n",
    $target,
    $pct,
    $covered,
    $statements
);
if ($pct + 0.0001 < $min) {
    fwrite(STDERR, sprintf("check-plugin-coverage: FAIL (minimum %.2f%%)\n", $min));
    exit(1);
}
fwrite(STDERR, sprintf("check-plugin-coverage: PASS (minimum %.2f%%)\n", $min));
PHP
