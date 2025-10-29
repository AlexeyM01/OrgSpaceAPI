#!/bin/sh

echo "Ждём БД..."
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
  sleep 2
done
echo "БД готова"

echo "Запускаем миграции Alembic"
alembic upgrade head

echo "Запускаем Uvicorn"
exec "$@"
