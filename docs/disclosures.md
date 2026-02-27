# Disclosures

The problem with having code secrets in `.env` files is that not only is there the risk of accidentally leaking them into a shared repository, but with LLMs able to access the local filesystem, some of these secrets could inadvertently make their way into training sets.

It's also _really_ hard to make sure they're kept consistent and uptodate across different projects and shared teams. Fortunately, local secure keychains are now available across all major OS platforms. 

I built this for a solo project covering many domains and languages: web (Vue.js), cross-platform desktop app (Rust+Tauri), background privileged system services (Rust), firmware (C/C++), and serverless (CDK with Typescript, Python lambdas), as well as a variety of toolchains (esp-idf, python, rust, npm/typescript, CDK) and build tools (Github Actions, CodeBuild CI/CD, Makefiles).

Storing and managing all the secrets inside `.env` files just became untenable. Each domain needed its own set of different settings, and different values would be needed across various stages of development (i.e. _dev, test, qa, prod_). Also, as these variables evolve, there would be a need for fine-grain versioning at the individual item level.

My own needs were very specific: I wanted it to use my local Mac keychain, build and flash to ESP32 devices, package and sign for various OSes (Mac, Linux, Windows), and deploy to AWS serverless.

When developing this, I wanted to maintain backward compatibility with `.env` and Python `dotenv` SDK, But I also wanted to offer coverage for other cloud providers that I personally had no experience with. Mainly, I wanted something others could use and integrate into their day-to-day lives.

I'm hoping others will test this out with their favorite cloud-service providers and contribute fixes and PRs. The section on testing covers how to enable tests for different platforms. These are currently mocked.

The section on `services` covers how to plug in other service providers. If you do decide to add your own, please make sure to include tests specific to them and include the test run results in PRs. I will likely have no way to validate the tests and will have to trust that your own backend service.

I'll try to set up automated testing as part of the release, but it may not be viable to run against every remote backend service.

## On Python

I chose Python, mainly because it already had a cross-platform, [keyring](https://pypi.org/project/keyring/) local keychain library, and most cloud-providers have SDKs that allow direct access to their secrets managers. 

However, it was awfully tempting to make it be a native standalone executable via Rust. There is a corresponding [keyring](https://docs.rs/keyring/latest/keyring/) but the cloud-service SDKs weren't just there, and that meant the daunting prospect of reverse-engineering an awful lot of cloud-service calls.

In the future, as Rust coverage grows, it may be worth moving to make it a standalone executable withuot external runtime dependencies. 

## On Vibe-coding

I've personally built multiple CLI-based tools using the same stack here, and created simpler versions of this for a number of internal projects. 

For this version, however, I made use of both locally run and remote LLMs, essentially as scribe/transcribers. These were all manually controlled with small, precise instructions at all times.

The local stack was run on an NVidia DGX Spark using the latest (as of this writing) Qwen model via vLLM. It ran great, but would sometimes get into loops. And the Spark would overheat a little (my solo project was to keep an eye on all this). 

For remote LLMs, I used Cursor, primarily with Claude Opus 4.6.

LLMs were also used to generate tests (again, under very specific, tight instructions), augmented by hand-made integration tests.

Also creation of mechanical parts of some of the docs, like examples, references, etc. were done by LLMs. I hand-wrote the first draft of the docs, but as it got larger and more cumbersome, I asked an LLM to refactor it and expand the contents. I hand-generated all the illustrations and screenshots and reviewed the contents.

Having said that, all mistakes and errors are mine.
