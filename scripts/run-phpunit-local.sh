#!/usr/bin/env bash
# Run PHPUnit integration tests locally using the same pattern as qa.yml (Option A).
# Usage: from repository root — ./scripts/run-phpunit-local.sh
#
# Requires: composer, curl, bash. Isolated MySQL on 127.0.0.1:3307 by default (root/root,
# db wordpress_test) via Docker mysql:5.7 — avoids LocalWP/other MySQL on :3306.
# Override with MYSQL_PORT=3306 only if you intend to use that server. Subversion (svn) required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WP_TESTS_DIR="${WP_TESTS_DIR:-/tmp/wordpress-tests-lib}"
export WP_TESTS_DIR
export WP_INSTALL_TESTS_SKIP_UPDATE_CHECK="${WP_INSTALL_TESTS_SKIP_UPDATE_CHECK:-true}"

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3307}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASS="${MYSQL_PASS:-root}"
MYSQL_DB="${MYSQL_DB:-wordpress_test}"
DOCKER_CONTAINER="${DOCKER_CONTAINER:-rank-math-api-phpunit-mysql}"

die() {
	echo "run-phpunit-local: $*" >&2
	exit 1
}

if [ ! -f "phpunit.xml.dist" ] || [ ! -f "tests/bootstrap.php" ]; then
	die "Run from the plugin repository root (missing phpunit.xml.dist or tests/bootstrap.php)."
fi

if ! command -v composer >/dev/null 2>&1; then
	die "composer not found in PATH. Install Composer: https://getcomposer.org/"
fi

if [ ! -f "vendor/autoload.php" ]; then
	echo "run-phpunit-local: vendor/ missing — running composer install"
	composer install --no-interaction --prefer-dist --no-progress
fi

mysql_ping() {
	if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$DOCKER_CONTAINER"; then
		docker exec "$DOCKER_CONTAINER" mysqladmin ping -h127.0.0.1 -u"$MYSQL_USER" -p"$MYSQL_PASS" --silent 2>/dev/null
		return $?
	fi
	if command -v mysqladmin >/dev/null 2>&1; then
		mysqladmin ping -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASS" --silent 2>/dev/null
		return $?
	fi
	return 1
}

wait_for_mysql() {
	local attempt
	for attempt in $(seq 1 30); do
		if mysql_ping; then
			return 0
		fi
		sleep 2
	done
	return 1
}

ensure_mysql() {
	if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$DOCKER_CONTAINER"; then
		if mysql_ping; then
			echo "run-phpunit-local: Docker MySQL ready at ${MYSQL_HOST}:${MYSQL_PORT} (db=${MYSQL_DB})"
			return 0
		fi
	fi

	if ! command -v docker >/dev/null 2>&1; then
		die "Docker is required for the default isolated test MySQL on port ${MYSQL_PORT} (avoids LocalWP on :3306). Install Docker or set MYSQL_PORT/MYSQL_HOST to a dedicated test server."
	fi

	if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$DOCKER_CONTAINER"; then
		echo "run-phpunit-local: starting existing Docker container ${DOCKER_CONTAINER}"
		docker start "$DOCKER_CONTAINER" >/dev/null
	else
		echo "run-phpunit-local: starting isolated mysql:5.7 on ${MYSQL_HOST}:${MYSQL_PORT} (root/root, db=${MYSQL_DB}; not LocalWP :3306)"
		DOCKER_PLATFORM=()
		if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
			DOCKER_PLATFORM=(--platform linux/amd64)
			echo "run-phpunit-local: arm64 host — using linux/amd64 platform for mysql:5.7 (matches qa.yml image via emulation)"
		fi
		docker run -d "${DOCKER_PLATFORM[@]}" --name "$DOCKER_CONTAINER" \
			-e MYSQL_ROOT_PASSWORD="$MYSQL_PASS" \
			-e MYSQL_DATABASE="$MYSQL_DB" \
			-p "${MYSQL_PORT}:3306" \
			mysql:5.7 >/dev/null
	fi

	if ! wait_for_mysql; then
		die "MySQL did not become ready within 60s. Check: docker logs ${DOCKER_CONTAINER}"
	fi
	echo "run-phpunit-local: Docker MySQL ready"
}

maybe_add_docker_mysql_path() {
	if command -v mysql >/dev/null 2>&1; then
		return 0
	fi
	if ! command -v docker >/dev/null 2>&1; then
		return 0
	fi
	if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$DOCKER_CONTAINER"; then
		return 0
	fi

	WRAPPER_DIR="$(mktemp -d "${TMPDIR:-/tmp}/rank-math-api-mysql.XXXXXX")"
	cat >"$WRAPPER_DIR/mysql" <<'WRAPPER_EOF'
#!/usr/bin/env bash
# Proxy mysql CLI to the isolated test container; strip host/port meant for host-side TCP.
set -euo pipefail
CONTAINER="__DOCKER_CONTAINER__"
MYSQL_USER="__MYSQL_USER__"
MYSQL_PASS="__MYSQL_PASS__"
filtered=()
skip=0
for arg in "$@"; do
	if [ "$skip" -gt 0 ]; then
		skip=$((skip - 1))
		continue
	fi
	case "$arg" in
		--host=*|--port=*|--protocol=*|--user=*|--password=*|-h*|-P*) continue ;;
		--host|--port|--protocol|--user|--password) skip=1; continue ;;
	esac
	filtered+=("$arg")
done
exec docker exec -i "$CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASS" "${filtered[@]}"
WRAPPER_EOF
	cat >"$WRAPPER_DIR/mysqladmin" <<'WRAPPER_EOF'
#!/usr/bin/env bash
set -euo pipefail
CONTAINER="__DOCKER_CONTAINER__"
MYSQL_USER="__MYSQL_USER__"
MYSQL_PASS="__MYSQL_PASS__"
filtered=()
skip=0
for arg in "$@"; do
	if [ "$skip" -gt 0 ]; then
		skip=$((skip - 1))
		continue
	fi
	case "$arg" in
		--host=*|--port=*|--protocol=*|--user=*|--password=*|-h*|-P*) continue ;;
		--host|--port|--protocol|--user|--password) skip=1; continue ;;
	esac
	filtered+=("$arg")
done
exec docker exec -i "$CONTAINER" mysqladmin -u"$MYSQL_USER" -p"$MYSQL_PASS" "${filtered[@]}"
WRAPPER_EOF
	sed -i.bak \
		-e "s/__DOCKER_CONTAINER__/${DOCKER_CONTAINER}/g" \
		-e "s/__MYSQL_USER__/${MYSQL_USER}/g" \
		-e "s/__MYSQL_PASS__/${MYSQL_PASS}/g" \
		"$WRAPPER_DIR/mysql" "$WRAPPER_DIR/mysqladmin"
	rm -f "$WRAPPER_DIR/mysql.bak" "$WRAPPER_DIR/mysqladmin.bak"
	chmod +x "$WRAPPER_DIR/mysql" "$WRAPPER_DIR/mysqladmin"
	export PATH="$WRAPPER_DIR:$PATH"
	echo "run-phpunit-local: using docker exec mysql client wrappers (host mysql CLI not found)"
}

ensure_mysql
maybe_add_docker_mysql_path

reset_test_database() {
	echo "run-phpunit-local: dropping test database ${MYSQL_DB} inside Docker only (if present)"
	if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$DOCKER_CONTAINER"; then
		die "Cannot reset ${MYSQL_DB}: Docker container ${DOCKER_CONTAINER} is not running"
	fi
	docker exec "$DOCKER_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASS" \
		-e "DROP DATABASE IF EXISTS \`${MYSQL_DB}\`;"
}

patch_wp_tests_db_host() {
	local config="${WP_TESTS_DIR}/wp-tests-config.php"
	if [ ! -f "$config" ]; then
		return 0
	fi
	# PHPUnit runs on the host; tests must reach Docker via the published port.
	if grep -q "define( 'DB_HOST'" "$config"; then
		sed -i.bak "s/define( 'DB_HOST', '[^']*' );/define( 'DB_HOST', '${MYSQL_HOST}:${MYSQL_PORT}' );/" "$config"
		rm -f "${config}.bak"
	fi
}

if ! command -v svn >/dev/null 2>&1; then
	die "subversion (svn) not found. install-wp-tests.sh needs svn to download the WordPress test library. On macOS: brew install subversion"
fi

INSTALL_SCRIPT="/tmp/install-wp-tests-rank-math-api.sh"
echo "run-phpunit-local: downloading install-wp-tests.sh (same source as qa.yml)"
curl -fsSL https://raw.githubusercontent.com/wp-cli/scaffold-command/main/templates/install-wp-tests.sh -o "$INSTALL_SCRIPT"

reset_test_database

echo "run-phpunit-local: installing WordPress test suite to ${WP_TESTS_DIR}"
# Host:port is written into wp-tests-config for host-side PHPUnit; mysql wrappers talk inside Docker.
bash "$INSTALL_SCRIPT" "$MYSQL_DB" "$MYSQL_USER" "$MYSQL_PASS" "${MYSQL_HOST}:${MYSQL_PORT}" latest
patch_wp_tests_db_host

if [ ! -d "$WP_TESTS_DIR" ] || [ ! -r "$WP_TESTS_DIR/includes/bootstrap.php" ]; then
	die "WordPress test bootstrap missing at ${WP_TESTS_DIR}/includes/bootstrap.php after install-wp-tests.sh"
fi

echo "run-phpunit-local: running vendor/bin/phpunit --configuration phpunit.xml.dist"
vendor/bin/phpunit --configuration phpunit.xml.dist
