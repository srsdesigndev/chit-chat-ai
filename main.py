import os
import sys
import json
import threading
import time
import random
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

# ---------- CONFIG ----------
THREAD_FILE = Path("thread.json")
MODEL = "claude-sonnet-4-20250514"
MAX_WORD_LIMIT = 500
BOX_WIDTH = 70
BIT_LENGTH = 64
BIT_SPEED = 0.01

# ---------- ANSI COLORS ----------
GREEN = "\033[92m"
CYAN = "\033[96m"
GRAY = "\033[90m"
RESET = "\033[0m"

load_dotenv()


class BitsLoader:
    """Animated binary loader for visual feedback during API calls."""
    
    def __init__(self, length=BIT_LENGTH, speed=BIT_SPEED):
        self.length = length
        self.speed = speed
        self._running = False
        self._thread = None

    def _animate(self):
        """Generate random binary animation."""
        while self._running:
            bits = "".join(random.choices("01", k=self.length))
            print(f"\r{GRAY}{bits}{RESET}", end="", flush=True)
            time.sleep(self.speed)

    def __enter__(self):
        """Start loader using context manager."""
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args):
        """Stop loader and clear line."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        print(f"\r{' ' * self.length}\r", end="", flush=True)


def print_boxed(text):
    """Print text in a rounded box."""
    top = f"╭{'─' * (BOX_WIDTH - 2)}╮"
    bottom = f"╰{'─' * (BOX_WIDTH - 2)}╯"
    print(f"{GREEN}{top}{RESET}")
    
    # Word wrap
    words = text.split()
    line = []
    for word in words:
        test_line = " ".join(line + [word])
        if len(test_line) <= BOX_WIDTH - 4:
            line.append(word)
        else:
            print(f"{GREEN}│ {RESET}{' '.join(line).ljust(BOX_WIDTH - 4)}{GREEN} │{RESET}")
            line = [word]
    
    if line:
        print(f"{GREEN}│ {RESET}{' '.join(line).ljust(BOX_WIDTH - 4)}{GREEN} │{RESET}")
    print(f"{GREEN}{bottom}{RESET}")

class ChitChat:
    """Conversational AI bot with persistent chat history."""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=api_key)
        self.system_prompt = (
            f"You are ChitChat. Answer in less than {MAX_WORD_LIMIT} words. "
            "Be clear and concise."
        )

    def _load_thread(self):
        """Load conversation history from file."""
        if not THREAD_FILE.exists():
            return []
        
        try:
            with THREAD_FILE.open() as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []

    def _save_thread(self, messages):
        """Save conversation history to file."""
        with THREAD_FILE.open("w") as f:
            json.dump(messages, f, indent=2)

    def _truncate_reply(self, text):
        """Enforce word limit on response."""
        words = text.split()
        return " ".join(words[:MAX_WORD_LIMIT]) if len(words) > MAX_WORD_LIMIT else text

    def ask(self, query):
        """Send query and display response."""
        history = self._load_thread()
        history.append({"role": "user", "content": query})

        try:
            with BitsLoader():
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=300,
                    system=self.system_prompt,
                    messages=history
                )

            reply = self._truncate_reply(response.content[0].text.strip())
            history.append({"role": "assistant", "content": reply})
            self._save_thread(history)
            print_boxed(reply)
            print()

        except Exception as e:
            print(f"\n{CYAN}Error: {e}{RESET}")
            sys.exit(1)


def main():
    """Entry point for CLI."""
    if len(sys.argv) < 2:
        print(f"{CYAN}Usage: ./query.sh \"your question\"{RESET}")
        sys.exit(1)

    bot = ChitChat()
    bot.ask(sys.argv[1])


if __name__ == "__main__":
    main()