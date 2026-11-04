# REST bootstrap

Source:
- Path: `rank-math.php`
- Lines: `343-358`
- Symbol: `RankMath::init_rest_api()`

```php
/**
 * Load the REST API endpoints.
 */
public function init_rest_api() {
	$controllers = [
		new \RankMath\Rest\Admin(),
		new \RankMath\Rest\Front(),
		new \RankMath\Rest\Shared(),
		new \RankMath\Rest\Post(),
		new \RankMath\Rest\Headless(),
		new \RankMath\Rest\Setup_Wizard(),
	];

	foreach ( $controllers as $controller ) {
		$controller->register_routes();
	}
}
```

Why it matters:
- all core Rank Math REST routes start here
- this is the fastest anchor point when tracing route ownership
