#!/usr/bin/env python3
import subprocess
import sys
import argparse
import os

def run_tests(test_command):
    """
    Runs the given test command and captures the output.
    Returns (success: bool, failure_output: str)
    """
    print(f"==> Running validation: {test_command}")

    # We run the test command using a shell to allow `npm test` or `pytest`
    process = subprocess.Popen(
        test_command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    output = []
    for line in process.stdout:
        print(line, end="")
        output.append(line)

    process.wait()

    full_output = "".join(output)

    # Simple heuristic to grab the bottom portion (often where failures are)
    # If output is too large, we truncate
    max_lines = 100
    lines = full_output.splitlines()
    if len(lines) > max_lines:
        truncated_output = "\n".join(lines[-max_lines:])
        formatted_output = f"...[Truncated]...\n{truncated_output}"
    else:
        formatted_output = full_output

    return process.returncode == 0, formatted_output

def generate_correction_prompt(failure_output):
    """
    Generates a prompt formatted for an LLM to correct the error.
    """
    prompt = (
        "The automated tests failed after your previous changes. "
        "Please fix the code so that the tests pass.\n\n"
        "Here is the test failure output:\n"
        "```\n"
        f"{failure_output}\n"
        "```\n"
    )
    return prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests and generate an LLM correction prompt on failure.")
    parser.add_argument("command", type=str, nargs="?", default="npm test", help="Test command to run (e.g. 'npm test').")
    parser.add_argument("--out", type=str, default="correction_prompt.txt", help="File to write the correction prompt to on failure.")

    args = parser.parse_args()

    success, failure_output = run_tests(args.command)

    if success:
        print("==> Tests passed successfully!")
        sys.exit(0)
    else:
        print(f"==> Tests failed. Generating correction prompt in {args.out}")
        prompt = generate_correction_prompt(failure_output)
        with open(args.out, "w") as f:
            f.write(prompt)
        sys.exit(1)
