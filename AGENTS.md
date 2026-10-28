# AGENTS.md

## Project
- Laravel 12 inventory management app (see `playground/README.md`).
- App code in `playground/` (not repo root). All commands run from `playground/` unless stated otherwise.

## Tech
- PHP 8.2+, Laravel 12, Livewire 3, Alpine.js
- Tailwind CSS 3, Vite 7, ApexCharts, PowerGrid
- DB: MySQL/SQLite; tests use SQLite in-memory (`playground/phpunit.xml`)

## Setup
**Docker (from repo root):**
```bash
docker compose up --build -d  # see playground/README.md for details
```
**Manual (from `playground/`):**
```bash
composer install
cp .env.example .env && php artisan key:generate
# configure DB in .env
php artisan migrate:fresh --seed
php artisan storage:link
npm install && npm run build
php artisan serve
```

## Dev
From `playground/`:
```bash
composer run dev  # runs server, queue, pail, vite via concurrently
npm run dev        # vite only
php artisan serve  # app only
```
Default creds: admin/password.

## Tests
From `playground/`:
```bash
composer test  # clears config, runs php artisan test
php artisan test  # run all
php artisan test --testsuite=Feature
php artisan test --testsuite=Unit
php artisan test tests/Feature/Auth/AuthenticationTest.php  # single file
```
Env preconfigured for testing (sqlite :memory:, array drivers).

## Build/Lint/Format
From `playground/`:
```bash
npm run build  # vite build
./vendor/bin/pint  # Laravel Pint (format)
```
No explicit lint script in package.json; use Pint for PHP formatting.

## Structure
- `app/Services/*`, `app/Models/*`, `app/Http/Controllers/*`, `app/Livewire/*` (views in `resources/views/livewire/`)
- `app/Helpers/CurrencyHelper.php` autoloaded via composer files
- Routes: `routes/web.php`, `routes/auth.php`; Breeze auth scaffolding present
- Helpers: currency formatting is global/dynamic (see README)

## Gotchas
- Working dir is `playground/` for app commands.
- Docker uses PostgreSQL service; manual uses MySQL/SQLite as configured.
- `composer run dev` uses `pail` for logs and queue listener.
- PowerGrid + Livewire used for data tables; currency helper affects global formatting.
- Tests run with array/cache/session/mail drivers and in-memory sqlite.
