#!/usr/bin/env python3
import subprocess
import sys
import argparse

def run_goose(instruction, system_prompt=None):
    """
    Runs Goose in a one-shot headless mode.
    Goose CLI supports a headless run by using 'goose session headless "instruction"'
    (or similar depending on the exact implementation in the goose CLI).
    We'll use 'goose run "instruction"' as the standard headless execution path.
    """
    cmd = ["goose", "run"]

    if system_prompt:
        # Depending on Goose CLI options, this might be --system or passed differently
        # Assuming --system based on standard agent CLIs
        cmd.extend(["--system", system_prompt])

    cmd.append(instruction)

    print(f"==> Running Goose with instruction: {instruction}")
    try:
        # Run goose as a subprocess, streaming output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            print(line, end="")

        process.wait()
        return process.returncode

    except FileNotFoundError:
        print("Error: 'goose' command not found. Ensure Goose is installed and in your PATH.")
        return 1
    except Exception as e:
        print(f"Error executing Goose: {e}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wrapper for running Goose unattended.")
    parser.add_argument("instruction", type=str, help="The instruction to execute.")
    parser.add_argument("--system", type=str, help="Optional system prompt to pass to Goose.", default=None)

    args = parser.parse_args()

    # If --system is not provided via CLI, we can attempt to read from RULES.md
    system_prompt = args.system
    if not system_prompt:
        try:
            with open("RULES.md", "r") as f:
                system_prompt = f.read()
                print("==> Loaded system prompt from RULES.md")
        except FileNotFoundError:
            pass

    exit_code = run_goose(args.instruction, system_prompt)
    sys.exit(exit_code)
