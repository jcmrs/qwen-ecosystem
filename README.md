# Qwen Ecosystem

Welcome to the qwen-ecosystem project - a comprehensive ecosystem implementation for Universal Tool Calling Protocol (UTCP) related projects and tools.

## Project Structure

This repository serves as a meta-repository containing multiple UTCP-related projects as git submodules in the `UPSTREAM/` directory, along with additional ecosystem tools and resources.

### Directories

- `.bootstrap/` - Bootstrap package for meta-systems ecosystem implementation
- `.utcp-kb/` - Knowledge base focused on UTCP, created from upstream clones and optimized for AI
- `UPSTREAM/` - Local upstream clones of relevant remote repositories (managed as git submodules)

### UPSTREAM Projects

The following UTCP-related projects are included as git submodules:

- [agent-implementation-example](UPSTREAM/agent-implementation-example) - Example implementation of UTCP agent
- [benchmarks](UPSTREAM/benchmarks) - UTCP performance benchmarks
- [chat-utcp](UPSTREAM/chat-utcp) - Chat interface for UTCP
- [code-mode](UPSTREAM/code-mode) - UTCP code mode implementation
- [elixir-utcp](UPSTREAM/elixir-utcp) - Elixir implementation of UTCP
- [go-utcp](UPSTREAM/go-utcp) - Go implementation of UTCP
- [go-utcp-mcp-bridge](UPSTREAM/go-utcp-mcp-bridge) - Go UTCP to MCP bridge
- [langchain-utcp-adapters](UPSTREAM/langchain-utcp-adapters) - Langchain adapters for UTCP
- [pydantic-ai-utcp](UPSTREAM/pydantic-ai-utcp) - Pydantic AI UTCP adapters
- [python-utcp](UPSTREAM/python-utcp) - Python implementation of UTCP
- [rs-utcp](UPSTREAM/rs-utcp) - Rust implementation of UTCP
- [strands-utcp](UPSTREAM/strands-utcp) - Strands UTCP integration
- [typescript-utcp](UPSTREAM/typescript-utcp) - TypeScript implementation of UTCP
- [utcp-agent](UPSTREAM/utcp-agent) - UTCP agent implementation
- [utcp-examples](UPSTREAM/utcp-examples) - UTCP examples
- [utcp-mcp](UPSTREAM/utcp-mcp) - UTCP MCP bridge
- [utcp-specification](UPSTREAM/utcp-specification) - UTCP specification

## Git Workflow

This repository uses Git Flow branching model:

- `master` - Production-ready code
- `develop` - Development branch
- `feature/*` - Feature branches
- `release/*` - Release preparation branches
- `hotfix/*` - Hotfix branches

## Git Submodules

The UPSTREAM directory contains git submodules that track the upstream repositories. To update submodules:

```bash
git submodule update --remote
```

To initialize submodules after cloning:

```bash
git submodule update --init --recursive
```

## Contributing

1. Create a feature branch: `git flow feature start <feature-name>`
2. Make your changes
3. Commit your changes: `git commit -m "Description of changes"`
4. Finish the feature: `git flow feature finish <feature-name>`
5. Push to the remote repository

## License

This project is part of the UTCP ecosystem. Individual projects may have their own licenses - please check the respective submodule directories for licensing information.