import os
import sys
import json
import threading
import time
import random
from anthropic import Anthropic
from dotenv import load_dotenv

# ---------- CONFIG ----------
THREAD_FILE = "thread.json"
MODEL = "claude-sonnet-4-20250514"
MAX_WORD_LIMIT = 100
BOX_WIDTH = 70
BIT_LENGTH = 64  # length of bits loader
BIT_SPEED = 0.01
# ----------------------------

# ---------- ANSI COLORS ----------
GREEN = "\033[92m"
CYAN = "\033[96m"
GRAY = "\033[90m"
RESET = "\033[0m"

load_dotenv()

# ---------- Bits Loader ----------
class BitsLoader:
    def __init__(self, length=BIT_LENGTH, speed=BIT_SPEED):
        self.length = length
        self.speed = speed
        self.running = False
        self.thread = threading.Thread(target=self.animate)

    def animate(self):
        while self.running:
            bits = "".join(random.choice("01") for _ in range(self.length))
            print(f"\r{GRAY}{bits}{RESET}", end="", flush=True)
            time.sleep(self.speed)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
        print("\r" + " " * self.length + "\r", end="", flush=True)


# ---------- Rounded Box Printer ----------
def print_boxed(text):
    top = f"╭{'─' * (BOX_WIDTH - 2)}╮"
    bottom = f"╰{'─' * (BOX_WIDTH - 2)}╯"
    print(GREEN + top + RESET)

    words = text.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= BOX_WIDTH - 4:
            line += word + " "
        else:
            print(f"{GREEN}│ {RESET}{line.ljust(BOX_WIDTH - 4)}{GREEN} │{RESET}")
            line = word + " "
    if line:
        print(f"{GREEN}│ {RESET}{line.ljust(BOX_WIDTH - 4)}{GREEN} │{RESET}")

    print(GREEN + bottom + RESET)


# ---------- ChitChat Core ----------
class ChitChat:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY missing in .env")

        self.client = Anthropic(api_key=api_key)

    def load_thread(self):
        if not os.path.exists(THREAD_FILE):
            return []

        try:
            with open(THREAD_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            return []

    def save_thread(self, messages):
        with open(THREAD_FILE, "w") as f:
            json.dump(messages, f, indent=2)

    def ask(self, query):
        history = self.load_thread()
        history.append({"role": "user", "content": query})

        system_instruction = (
            f"You are ChitChat. "
            f"Answer in less than {MAX_WORD_LIMIT} words. "
            f"Be clear and concise."
        )

        loader = BitsLoader()
        loader.start()

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=300,
                system=system_instruction,
                messages=history
            )

            loader.stop()

            reply = response.content[0].text.strip()

            # enforce word limit
            words = reply.split()
            if len(words) > MAX_WORD_LIMIT:
                reply = " ".join(words[:MAX_WORD_LIMIT])

            history.append({"role": "assistant", "content": reply})
            self.save_thread(history)

            print_boxed(reply)
            print()

        except Exception as e:
            loader.stop()
            print(f"\nAPI Error: {e}")


# ---------- Entry ----------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{CYAN}Usage: ./query.sh \"your question\"{RESET}")
        sys.exit(1)

    query = sys.argv[1]

    bot = ChitChat()
    bot.ask(query)