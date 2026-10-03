// Railway build/deploy settings for the backend_django service.
//
// Railway does not read this file on deploy. Changes take effect only when applied:
//   cd .railway && npm install && cd ..
//   railway environment development && railway config plan   # dry run; must say "0 to destroy"
//   railway config apply
// and the same for production. The `partial` name scopes this file to the resources it
// declares, so the Postgres_db service and the frontend services are never touched.
import { defineRailway, github, preserve, project, service } from "railway/iac";

export const partial = "backend";

export default defineRailway((ctx) => {
  if (ctx.environment !== "development" && ctx.environment !== "production") {
    throw new Error(`Unexpected environment: ${ctx.environment}`);
  }
  const prod = ctx.environment === "production";

  const backend = service("backend_django", {
    // checkSuites: deploy only after the GitHub CI checks pass.
    source: github("SevanBrodjian/SevanBNet-backend", {
      branch: prod ? "main" : "dev",
      checkSuites: true,
    }),
    build: { builder: "RAILPACK" },
    preDeploy: "python manage.py migrate --noinput",
    // collectstatic writes into the container, so it runs at start rather than pre-deploy.
    start:
      "python manage.py collectstatic --noinput && gunicorn sevanbnet.wsgi --bind 0.0.0.0:$PORT --workers 2 --access-logfile -",
    healthcheck: "/healthz/",
    healthcheckTimeout: 60,
    // Values live in Railway; preserve() keeps whatever is set there.
    env: {
      DATABASE_URL: preserve(),
      DJANGO_SECRET_KEY: preserve(),
      DJANGO_DEBUG: preserve(),
      QR_BASE_URL: preserve(),
      PGDATABASE: preserve(),
      PGHOST: preserve(),
      PGPASSWORD: preserve(),
      PGPORT: preserve(),
      PGUSER: preserve(),
    },
  });

  return project("SevanBNet", { resources: [backend] });
});
