# Using enveloper inside Docker

This example shows how to make variables from the **keychain** or **AWS** (or other backends) available inside a Docker container **without** baking a `.env` file into the image or bind-mounting one at runtime.

## Two approaches

### 1. Host loads secrets, then passes them into the container

The host has enveloper and the keychain (or cloud) configured. You load secrets into the host environment, then pass those env vars into `docker run` so the container never sees a `.env` file.

```bash
# On the host: load from keychain (or use --service aws after pull)
eval "$(enveloper --domain mydomain --project myproject export --format unix)"

# Run the container; pass through the variables (no .env file)
docker run --rm -e MY_API_KEY -e MY_API_SECRET -e LEVEL_SET myapp:latest
```

The container only receives the variables as environment; the image stays free of secret files.

### 2. Container pulls from AWS at startup

The image includes enveloper and AWS credentials (or an IAM role). At container start, it pulls from AWS SSM and runs `export` so the app sees the variables. No `.env` in the image.

- **Dockerfile**: installs `enveloper[aws]`, sets `ENVELOPER_DOMAIN` / `ENVELOPER_PROJECT`, and uses an entrypoint that runs `enveloper pull`, then `eval "$(enveloper export --format unix)"`, then your app.
- **Runtime**: provide AWS credentials (e.g. `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) or run on ECS with a task role.

See the [Dockerfile](Dockerfile) and [entrypoint.sh](entrypoint.sh) in this folder.

## Integration with sample.env

1. **Import** the example set into keychain or AWS (from the repo root or `examples/`):

   ```bash
   enveloper import sample.env --domain mydomain --project myproject
   # If using AWS:
   enveloper push --service aws --domain mydomain --project myproject
   ```

2. **Export** (unix format) and run:

   - **Host-injected**:  
     `eval "$(enveloper --domain mydomain --project myproject export --format unix)"`  
     then `docker run -e MY_API_KEY -e MY_API_SECRET -e LEVEL_SET ...`

   - **Container**:  
     entrypoint runs `enveloper pull --service aws` then  
     `eval "$(enveloper --domain mydomain --project myproject export --format unix)"`  
     then your app.

3. **Unexport** (optional): on the host, after the container exits,  
   `eval "$(enveloper --domain mydomain --project myproject unexport --format unix)"`  
   to clear the variables from the host shell.

## Files in this folder

| File | Purpose |
|------|--------|
| [Dockerfile](Dockerfile) | Image with enveloper and entrypoint that pulls + exports then runs the app. |
| [entrypoint.sh](entrypoint.sh) | Pulls from AWS, runs `export`, then `exec` the main command. |
| [app.sh](app.sh) | Example app that prints (masked) env vars to show they are set. |

## Build and run (container pulls from AWS)

```bash
# Build (from this directory or project root)
docker build -f examples/docker/Dockerfile -t enveloper-demo .

# Run with AWS credentials so the container can pull from SSM
docker run --rm \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  -e ENVELOPER_DOMAIN=mydomain -e ENVELOPER_PROJECT=myproject \
  enveloper-demo
```

## Build and run (host injects from keychain)

```bash
# Host: load from keychain
eval "$(enveloper --domain mydomain --project myproject export --format unix)"

# Run container with env passed from host (use a minimal image or same image with custom entrypoint)
docker run --rm -e MY_API_KEY -e MY_API_SECRET -e LEVEL_SET enveloper-demo

# When done, clear host env (optional)
eval "$(enveloper --domain mydomain --project myproject unexport --format unix)"
```

For the host-inject case you can use a minimal image that only runs `app.sh` and pass env from the host; no need for enveloper inside the container.
