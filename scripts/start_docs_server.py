#!/usr/bin/env python3
"""Start docs-mcp-server with environment variables from .env."""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")


def main():
    """Start docs-mcp-server with configuration from .env."""
    # Get configuration from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    embedding_model = os.getenv("EMBEDDING_MODEL")

    if openai_key and openai_base_url:
        print("✅ Loaded OpenAI-compatible API credentials from .env")
        print(f"   Base URL: {openai_base_url}")
    else:
        print("⚠️  No OPENAI_API_KEY or OPENAI_BASE_URL found in .env")

    # Set embedding model if configured
    if embedding_model and openai_key:
        # Use openai: prefix since we're using OpenAI-compatible API
        embedding_arg = f"--embedding-model=openai:{embedding_model}"
        print(f"✅ Using embedding model: {embedding_model}")
    else:
        embedding_arg = None
        if not embedding_model:
            print("⚠️  No EMBEDDING_MODEL configured, using full-text search only")
        if not openai_key:
            print("⚠️  No OPENAI_API_KEY configured, using full-text search only")

    # Build command as shell string to use nvm's npx
    cmd_parts = ["npx", "@arabold/docs-mcp-server@latest"]

    if embedding_arg:
        cmd_parts.append(embedding_arg)

    # Add any additional arguments passed to this script
    cmd_parts.extend(sys.argv[1:])

    # Join into shell command
    cmd = " ".join(cmd_parts)

    print("\n🚀 Starting docs-mcp-server...")
    print("   Web interface: http://127.0.0.1:6280")
    print("   MCP endpoints: http://127.0.0.1:6280/mcp")
    print()

    # Run the server (environment already set by load_dotenv)
    try:
        subprocess.run(cmd, shell=True, check=True)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed with exit code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
