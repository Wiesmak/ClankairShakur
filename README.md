# Clankair Shakur

Discord bot for Umamusume: Pretty Derby related statistics.

## Features

- Discord slash commands
- PMF + CDF chart generation for a binomial distribution
- Optional concurrency limit for chart generation
- Container-ready build using UBI 9 + Python 3.14
- Kubernetes / OpenShift manifests in `k8s/`

## Requirements

- Python 3.14+
- A Discord bot token
- `uv` recommended for local development
- Docker / Podman for container builds
- Kubernetes or OpenShift for deployment

## Project structure

```text
src/clankair_shakur/
├── app.py          # bot entrypoint
├── settings.py     # environment-driven settings
└── cogs/
	└── pmf_cog.py  # /binomial pmf command

.tekton/
├── pipeline.yaml
└── pipelinerun.yaml

k8s/
├── configmap.yaml
├── deployment.yaml
├── imagestream.yaml
├── kustomization.yaml
└── serviceaccount.yaml
```

## Configuration

The bot reads the following environment variables:

- `DISCORD_TOKEN` - required Discord bot token
- `THREAD_LIMIT` - optional limit for concurrent chart generation jobs

The Kubernetes manifests expect a secret named `clankair-shakur` with the key `discord-token`.
The provided ConfigMap contains `thread-limit: "3"` by default.

## Local development

### 1. Clone the repository

```powershell
git clone https://github.com/wiesmak/clankairshakur.git
cd clankair-shakur
```

### 2. Create the virtual environment and install dependencies

Using `uv`:

```powershell
uv sync
```

If you prefer a standard Python workflow, install the project in editable mode after creating a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### 3. Set environment variables

PowerShell example:

```powershell
$env:DISCORD_TOKEN = "your-discord-bot-token"
$env:THREAD_LIMIT = "3"   # optional
```

### 4. Run the bot

With `uv`:

```powershell
uv run clankair-shakur
```

Or directly from the source tree:

```powershell
python -m clankair_shakur
```

The bot registers its slash commands on startup and loads `clankair_shakur.cogs.pmf_cog`.

## Local testing

At minimum, verify the application starts and reads configuration correctly:

```powershell
uv run clankair-shakur
```

If you want to sanity-check the chart generation code without Discord, you can import `create_pmf_graph` from `clankair_shakur.cogs.pmf_cog` in a Python shell and confirm it returns a PNG buffer.

## Docker image

The repository includes a multi-stage `Dockerfile` that builds the application on UBI 9 Python 3.14 and runs it on the minimal UBI 9 Python image.

### Build

```powershell
docker build -t clankair-shakur:1.0.0 .
```

### Run

```powershell
docker run --rm `
  -e DISCORD_TOKEN="your-discord-bot-token" `
  -e THREAD_LIMIT="3" `
  clankair-shakur:1.0.0
```

For Podman, use the same commands with `podman` instead of `docker`.

## Kubernetes deployment

The `k8s/` directory contains a Kustomize base with:

- `Deployment`
- `ServiceAccount`
- `ConfigMap`
- `ImageStream` for OpenShift

### Prerequisites

- A namespace/project already created
- A secret named `clankair-shakur` containing `discord-token`
- An image available in your registry or OpenShift internal registry

Create the token secret:

```powershell
kubectl create secret generic clankair-shakur `
  --from-literal=discord-token="your-discord-bot-token"
```

If you use OpenShift, you can replace `kubectl` with `oc`.

### Apply the manifests

```powershell
kubectl apply -k k8s/
```

Or on OpenShift:

```powershell
oc apply -k k8s/
```

### Notes about the manifests

- `k8s/deployment.yaml` expects the bot image to be available in the cluster registry.
- `k8s/configmap.yaml` sets `THREAD_LIMIT` through `thread-limit`.
- `k8s/serviceaccount.yaml` defines the service account used by the pod.
- `k8s/imagestream.yaml` is OpenShift-specific.
- `k8s/kustomization.yaml` applies common labels and image overrides.

Depending on your registry and namespace layout, you may need to adjust image references in:

- `k8s/deployment.yaml`
- `k8s/kustomization.yaml`

## OpenShift deployment flow

A typical OpenShift workflow looks like this:

1. Create or select a project.
2. Build and push the image into the OpenShift internal registry, or import it into an ImageStream.
3. Create the `clankair-shakur` secret containing `discord-token`.
4. Apply the Kustomize base from `k8s/`.

Example:

```powershell
oc new-project clankair-shakur
oc create secret generic clankair-shakur --from-literal=discord-token="your-discord-bot-token"
oc apply -k k8s/
```

If you want OpenShift to build the image, add your own BuildConfig or Tekton pipeline, then point the Deployment/ImageStream at the produced tag.

## Tekton CI/CD option

Tekton pipeline definitions are included in `.tekton/`:

- `.tekton/pipeline.yaml` defines a `Pipeline` named `build-clankair-shakur`
- `.tekton/pipelinerun.yaml` defines a sample `PipelineRun`

The pipeline uses the following steps:

- clone the repository with the `git-clone` ClusterTask
- build the container image with the `buildah` ClusterTask
- push the image to the OpenShift internal registry by default

The included `PipelineRun` uses the `pipeline` service account and a PVC-backed workspace for source checkout.

If you want to extend the pipeline, the current flow is a standard one:

1. Clone the repo.
2. Run `uv sync` or `pip install -e .`.
3. Build the container image.
4. Push the image to your registry.
5. Deploy with `kubectl apply -k k8s/` or `oc apply -k k8s/`.

Typical Tekton tasks you may want:

- checkout
- dependency validation / tests
- image build
- image push
- manifest deploy

If you change the Tekton pipeline or image tag, keep it in sync with `k8s/kustomization.yaml` and `k8s/deployment.yaml`.

## Argo CD option

Argo CD is also not bundled, but the repo works well as a GitOps source.

Recommended pattern:

1. Point Argo CD at this repository.
2. Configure the app path to `k8s/`.
3. Let Argo CD sync the manifests into your target namespace.
4. Manage the Discord token secret separately in the cluster.

Example application source path:

```text
k8s/
```

If you use Argo CD image updater or a CI pipeline, update the image tag in Kustomize when a new container is released.

## Runtime behavior

- The bot uses the command prefix `__`, but its main functionality is exposed through slash commands.
- On startup it loads the `binomial` command group and syncs the Discord application commands tree.
- The `/binomial pmf` command renders a PMF/CDF chart for a binomial distribution and sends it as a PNG.

## Troubleshooting

- **Bot does not start**: verify `DISCORD_TOKEN` is set and valid.
- **Slash commands do not appear**: check the bot has been invited with the correct application scopes and allow time for Discord command sync.
- **Chart generation is slow**: lower `THREAD_LIMIT` or keep it at the default `3`.
- **Container/pod exits immediately**: inspect logs; missing environment variables or registry/image issues are the most common causes.

## License

See the repository metadata or upstream project for licensing details.

